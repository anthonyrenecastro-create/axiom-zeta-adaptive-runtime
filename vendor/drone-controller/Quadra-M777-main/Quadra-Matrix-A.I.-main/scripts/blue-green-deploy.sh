#!/bin/bash
# Blue-Green Deployment Script

set -e

# Configuration
NAMESPACE="${NAMESPACE:-default}"
APP_NAME="quadra-matrix"
KUBECTL="${KUBECTL:-kubectl}"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_blue() {
    echo -e "${BLUE}[BLUE]${NC} $1"
}

# Get current active deployment
get_active_deployment() {
    local active=$($KUBECTL get service ${APP_NAME}-production -n ${NAMESPACE} \
        -o jsonpath='{.spec.selector.deployment}' 2>/dev/null || echo "blue")
    echo "$active"
}

# Get inactive deployment
get_inactive_deployment() {
    local active=$(get_active_deployment)
    if [ "$active" == "blue" ]; then
        echo "green"
    else
        echo "blue"
    fi
}

# Check deployment health
check_deployment_health() {
    local deployment=$1
    local deployment_name="${APP_NAME}-${deployment}"
    
    log_info "Checking health of ${deployment_name}..."
    
    # Wait for deployment to be ready
    $KUBECTL wait --for=condition=available --timeout=300s \
        deployment/${deployment_name} -n ${NAMESPACE}
    
    # Check pod status
    local ready_pods=$($KUBECTL get deployment ${deployment_name} -n ${NAMESPACE} \
        -o jsonpath='{.status.readyReplicas}')
    local desired_pods=$($KUBECTL get deployment ${deployment_name} -n ${NAMESPACE} \
        -o jsonpath='{.spec.replicas}')
    
    if [ "$ready_pods" == "$desired_pods" ]; then
        log_info "✓ All ${ready_pods}/${desired_pods} pods are ready"
        return 0
    else
        log_error "✗ Only ${ready_pods}/${desired_pods} pods are ready"
        return 1
    fi
}

# Run smoke tests
run_smoke_tests() {
    local deployment=$1
    local service_name="${APP_NAME}-${deployment}"
    
    log_info "Running smoke tests against ${deployment}..."
    
    # Get service endpoint
    local endpoint=$($KUBECTL get service ${service_name} -n ${NAMESPACE} \
        -o jsonpath='{.spec.clusterIP}')
    
    # Test health endpoint
    log_info "Testing /health endpoint..."
    $KUBECTL run curl-test-${RANDOM} --image=curlimages/curl:latest --rm -i --restart=Never \
        -n ${NAMESPACE} -- curl -f http://${endpoint}/health
    
    if [ $? -eq 0 ]; then
        log_info "✓ Health check passed"
    else
        log_error "✗ Health check failed"
        return 1
    fi
    
    # Test metrics endpoint
    log_info "Testing /metrics endpoint..."
    $KUBECTL run curl-test-${RANDOM} --image=curlimages/curl:latest --rm -i --restart=Never \
        -n ${NAMESPACE} -- curl -f http://${endpoint}/metrics
    
    if [ $? -eq 0 ]; then
        log_info "✓ Metrics endpoint accessible"
    else
        log_warn "⚠ Metrics endpoint check failed (non-critical)"
    fi
    
    return 0
}

# Switch traffic to new deployment
switch_traffic() {
    local target_deployment=$1
    
    log_info "Switching traffic to ${target_deployment} deployment..."
    
    # Update service selector
    $KUBECTL patch service ${APP_NAME}-production -n ${NAMESPACE} \
        -p "{\"spec\":{\"selector\":{\"deployment\":\"${target_deployment}\"}}}"
    
    log_info "✓ Traffic switched to ${target_deployment}"
}

# Rollback to previous deployment
rollback() {
    local active=$(get_active_deployment)
    local previous=$(get_inactive_deployment)
    
    log_warn "Rolling back from ${active} to ${previous}..."
    switch_traffic "$previous"
    log_info "✓ Rollback complete"
}

# Deploy new version
deploy() {
    local new_version=$1
    local inactive=$(get_inactive_deployment)
    local active=$(get_active_deployment)
    
    log_info "=== Starting Blue-Green Deployment ==="
    log_info "Active: ${active}"
    log_info "Target: ${inactive}"
    log_info "Version: ${new_version}"
    echo
    
    # Update inactive deployment with new version
    log_info "Updating ${inactive} deployment to version ${new_version}..."
    $KUBECTL set image deployment/${APP_NAME}-${inactive} \
        ${APP_NAME}=${APP_NAME}:${new_version} -n ${NAMESPACE}
    
    # Wait for rollout
    log_info "Waiting for ${inactive} deployment rollout..."
    $KUBECTL rollout status deployment/${APP_NAME}-${inactive} -n ${NAMESPACE}
    
    # Check health
    if ! check_deployment_health "$inactive"; then
        log_error "Health check failed for ${inactive} deployment"
        exit 1
    fi
    
    # Run smoke tests
    if ! run_smoke_tests "$inactive"; then
        log_error "Smoke tests failed for ${inactive} deployment"
        read -p "Continue with deployment? (yes/no): " continue_deploy
        if [ "$continue_deploy" != "yes" ]; then
            log_error "Deployment aborted"
            exit 1
        fi
    fi
    
    # Switch traffic
    read -p "Switch traffic to ${inactive} deployment? (yes/no): " confirm
    if [ "$confirm" == "yes" ]; then
        switch_traffic "$inactive"
        
        log_info "=== Deployment Complete ==="
        log_info "Traffic is now routed to ${inactive} deployment"
        log_info "Previous ${active} deployment is still running for rollback"
        echo
        log_warn "To rollback, run: $0 rollback"
        log_warn "To cleanup old deployment: kubectl delete deployment ${APP_NAME}-${active} -n ${NAMESPACE}"
    else
        log_info "Deployment staged but not activated"
        log_info "To activate: $0 switch ${inactive}"
    fi
}

# Main command handling
case "${1:-}" in
    deploy)
        if [ -z "${2:-}" ]; then
            log_error "Usage: $0 deploy <version>"
            exit 1
        fi
        deploy "$2"
        ;;
    
    switch)
        if [ -z "${2:-}" ]; then
            target=$(get_inactive_deployment)
        else
            target="$2"
        fi
        switch_traffic "$target"
        ;;
    
    rollback)
        rollback
        ;;
    
    status)
        active=$(get_active_deployment)
        inactive=$(get_inactive_deployment)
        
        echo "=== Blue-Green Deployment Status ==="
        echo
        log_blue "Active Deployment: ${active}"
        $KUBECTL get deployment ${APP_NAME}-${active} -n ${NAMESPACE}
        echo
        log_blue "Inactive Deployment: ${inactive}"
        $KUBECTL get deployment ${APP_NAME}-${inactive} -n ${NAMESPACE}
        echo
        log_blue "Production Service:"
        $KUBECTL get service ${APP_NAME}-production -n ${NAMESPACE}
        ;;
    
    test)
        deployment="${2:-$(get_inactive_deployment)}"
        run_smoke_tests "$deployment"
        ;;
    
    *)
        echo "Blue-Green Deployment Manager"
        echo
        echo "Usage: $0 <command> [options]"
        echo
        echo "Commands:"
        echo "  deploy <version>   Deploy new version to inactive environment"
        echo "  switch [blue|green] Switch traffic to specified deployment"
        echo "  rollback           Rollback to previous deployment"
        echo "  status             Show current deployment status"
        echo "  test [deployment]  Run smoke tests against deployment"
        echo
        echo "Environment Variables:"
        echo "  NAMESPACE          Kubernetes namespace (default: default)"
        echo "  KUBECTL            kubectl command (default: kubectl)"
        echo
        echo "Examples:"
        echo "  $0 deploy 1.1.0"
        echo "  $0 switch green"
        echo "  $0 rollback"
        echo "  $0 status"
        exit 1
        ;;
esac
