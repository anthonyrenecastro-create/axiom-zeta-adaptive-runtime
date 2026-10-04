#!/bin/bash
# Canary Deployment Script

set -e

# Configuration
NAMESPACE="${NAMESPACE:-default}"
APP_NAME="quadra-matrix"
KUBECTL="${KUBECTL:-kubectl}"
STABLE_DEPLOYMENT="${APP_NAME}-stable"
CANARY_DEPLOYMENT="${APP_NAME}-canary"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get current replica counts
get_replicas() {
    local deployment=$1
    $KUBECTL get deployment ${deployment} -n ${NAMESPACE} \
        -o jsonpath='{.spec.replicas}' 2>/dev/null || echo "0"
}

# Calculate traffic split
calculate_traffic_split() {
    local stable=$(get_replicas ${STABLE_DEPLOYMENT})
    local canary=$(get_replicas ${CANARY_DEPLOYMENT})
    local total=$((stable + canary))
    
    if [ $total -gt 0 ]; then
        local canary_percent=$((canary * 100 / total))
        echo "$canary_percent"
    else
        echo "0"
    fi
}

# Scale deployments for traffic split
scale_for_traffic_split() {
    local canary_percent=$1
    local total_replicas=${2:-10}
    
    # Calculate replica counts
    local canary_replicas=$((total_replicas * canary_percent / 100))
    local stable_replicas=$((total_replicas - canary_replicas))
    
    # Ensure at least 1 replica for each if not 0%
    if [ $canary_percent -gt 0 ] && [ $canary_replicas -eq 0 ]; then
        canary_replicas=1
        stable_replicas=$((total_replicas - 1))
    fi
    
    log_info "Scaling to ${canary_percent}% canary traffic..."
    log_info "Stable: ${stable_replicas} replicas, Canary: ${canary_replicas} replicas"
    
    # Scale stable
    $KUBECTL scale deployment ${STABLE_DEPLOYMENT} -n ${NAMESPACE} \
        --replicas=${stable_replicas}
    
    # Scale canary
    $KUBECTL scale deployment ${CANARY_DEPLOYMENT} -n ${NAMESPACE} \
        --replicas=${canary_replicas}
    
    # Wait for rollout
    $KUBECTL rollout status deployment ${STABLE_DEPLOYMENT} -n ${NAMESPACE} --timeout=300s
    $KUBECTL rollout status deployment ${CANARY_DEPLOYMENT} -n ${NAMESPACE} --timeout=300s
    
    log_info "✓ Traffic split updated to ${canary_percent}% canary"
}

# Monitor canary metrics
monitor_canary() {
    local duration=${1:-300}  # 5 minutes default
    
    log_info "Monitoring canary for ${duration} seconds..."
    
    # Get service endpoint
    local service_ip=$($KUBECTL get service ${APP_NAME}-service -n ${NAMESPACE} \
        -o jsonpath='{.status.loadBalancer.ingress[0].ip}' 2>/dev/null || echo "localhost")
    
    log_info "Endpoint: ${service_ip}"
    log_info "Collecting metrics..."
    
    local end_time=$(($(date +%s) + duration))
    local error_count=0
    local success_count=0
    
    while [ $(date +%s) -lt $end_time ]; do
        # Check health
        if curl -sf http://${service_ip}/health > /dev/null 2>&1; then
            ((success_count++))
        else
            ((error_count++))
        fi
        
        sleep 5
        
        # Show progress
        local elapsed=$(($(date +%s) - (end_time - duration)))
        local error_rate=0
        local total=$((error_count + success_count))
        if [ $total -gt 0 ]; then
            error_rate=$((error_count * 100 / total))
        fi
        
        echo -ne "\rElapsed: ${elapsed}s | Requests: ${total} | Errors: ${error_count} (${error_rate}%)   "
    done
    
    echo
    log_info "Monitoring complete"
    log_info "Total requests: $((error_count + success_count))"
    log_info "Successful: ${success_count}"
    log_info "Failed: ${error_count}"
    
    # Determine if canary is healthy
    local total=$((error_count + success_count))
    if [ $total -gt 0 ]; then
        local error_rate=$((error_count * 100 / total))
        if [ $error_rate -gt 5 ]; then
            log_error "✗ Canary error rate too high: ${error_rate}%"
            return 1
        else
            log_info "✓ Canary is healthy (error rate: ${error_rate}%)"
            return 0
        fi
    fi
    
    log_warn "⚠ Not enough data to determine canary health"
    return 0
}

# Gradual rollout
gradual_rollout() {
    local new_version=$1
    local stages=(10 25 50 75 100)
    
    log_info "=== Starting Canary Deployment ==="
    log_info "Version: ${new_version}"
    echo
    
    # Update canary deployment
    log_info "Updating canary deployment to version ${new_version}..."
    $KUBECTL set image deployment/${CANARY_DEPLOYMENT} \
        ${APP_NAME}=${APP_NAME}:${new_version} -n ${NAMESPACE}
    
    # Wait for rollout
    $KUBECTL rollout status deployment/${CANARY_DEPLOYMENT} -n ${NAMESPACE}
    
    # Gradual traffic shift
    for stage in "${stages[@]}"; do
        log_info "=== Stage ${stage}% ==="
        
        scale_for_traffic_split $stage
        
        # Monitor
        if ! monitor_canary 120; then  # 2 minutes per stage
            log_error "Canary deployment failed at ${stage}%"
            log_info "Rolling back..."
            scale_for_traffic_split 0
            return 1
        fi
        
        if [ $stage -ne 100 ]; then
            read -p "Continue to next stage? (yes/no/abort): " continue
            case "$continue" in
                yes) ;;
                no)
                    log_info "Paused at ${stage}%"
                    log_info "To continue: $0 promote ${stage}"
                    return 0
                    ;;
                abort)
                    log_info "Aborting deployment, rolling back..."
                    scale_for_traffic_split 0
                    return 1
                    ;;
            esac
        fi
    done
    
    # Promote canary to stable
    log_info "=== Promoting Canary to Stable ==="
    promote_canary "$new_version"
}

# Promote canary to stable
promote_canary() {
    local version=$1
    
    log_info "Promoting canary to stable..."
    
    # Update stable deployment to canary version
    $KUBECTL set image deployment/${STABLE_DEPLOYMENT} \
        ${APP_NAME}=${APP_NAME}:${version} -n ${NAMESPACE}
    
    # Scale stable back to full
    scale_for_traffic_split 0 10
    
    log_info "✓ Canary promoted to stable"
}

# Rollback canary
rollback_canary() {
    log_warn "Rolling back canary deployment..."
    scale_for_traffic_split 0
    log_info "✓ Canary rolled back"
}

# Main command handling
case "${1:-}" in
    deploy)
        if [ -z "${2:-}" ]; then
            log_error "Usage: $0 deploy <version>"
            exit 1
        fi
        gradual_rollout "$2"
        ;;
    
    scale)
        if [ -z "${2:-}" ]; then
            log_error "Usage: $0 scale <percent>"
            exit 1
        fi
        scale_for_traffic_split "$2"
        ;;
    
    monitor)
        duration="${2:-300}"
        monitor_canary "$duration"
        ;;
    
    promote)
        if [ -z "${2:-}" ]; then
            log_error "Usage: $0 promote <version>"
            exit 1
        fi
        promote_canary "$2"
        ;;
    
    rollback)
        rollback_canary
        ;;
    
    status)
        stable=$(get_replicas ${STABLE_DEPLOYMENT})
        canary=$(get_replicas ${CANARY_DEPLOYMENT})
        percent=$(calculate_traffic_split)
        
        echo "=== Canary Deployment Status ==="
        echo
        log_info "Traffic Split: ${percent}% canary"
        echo
        log_info "Stable Deployment:"
        $KUBECTL get deployment ${STABLE_DEPLOYMENT} -n ${NAMESPACE}
        echo
        log_info "Canary Deployment:"
        $KUBECTL get deployment ${CANARY_DEPLOYMENT} -n ${NAMESPACE}
        ;;
    
    *)
        echo "Canary Deployment Manager"
        echo
        echo "Usage: $0 <command> [options]"
        echo
        echo "Commands:"
        echo "  deploy <version>     Deploy new version with gradual rollout"
        echo "  scale <percent>      Set canary traffic percentage (0-100)"
        echo "  monitor [duration]   Monitor canary metrics (default: 300s)"
        echo "  promote <version>    Promote canary to stable"
        echo "  rollback             Rollback canary deployment"
        echo "  status               Show current deployment status"
        echo
        echo "Examples:"
        echo "  $0 deploy 1.1.0"
        echo "  $0 scale 25"
        echo "  $0 promote 1.1.0"
        echo "  $0 rollback"
        exit 1
        ;;
esac
