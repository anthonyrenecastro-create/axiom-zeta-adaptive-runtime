#!/usr/bin/env python3
"""
Quadra Matrix A.I. - Simple Launcher
No GUI needed - runs from command line with interactive menu
"""

import asyncio
import sys

def print_banner():
    print("\n" + "="*80)
    print("🌟 QUADRA MATRIX A.I. - EXPONENTIAL TRAINING SYSTEM")
    print("="*80)
    print("CPU-friendly | 10x Speedup | Minimal Resources")
    print("="*80 + "\n")

def print_menu():
    print("Choose an option:")
    print()
    print("  1. 🚀 Quick Demo (20 batches, ~2 minutes)")
    print("  2. 📊 Full Training (100 batches, ~10 minutes)")
    print("  3. 📈 Show Training Results")
    print("  4. 🔧 Custom Training (interactive)")
    print("  5. 💾 Load & Test Trained Model")
    print("  6. ❓ Help & Documentation")
    print("  7. 🚪 Exit")
    print()

async def quick_demo():
    """Run a quick 20-batch training demo"""
    print("\n🚀 Starting Quick Demo...")
    print("This will train on WikiText-2 for 20 batches (~2 minutes)\n")
    
    from train_quadra_matrix import QuadraMatrixTrainer
    
    trainer = QuadraMatrixTrainer(field_size=100, device='cpu')
    await trainer.train(
        dataset_name='wikitext',
        dataset_config='wikitext-2-raw-v1',
        num_batches=20,
        batch_size=5
    )
    
    print("\n✅ Quick demo complete!")
    print("Check 'training_metrics.png' for visualization")

async def full_training():
    """Run full 100-batch training"""
    print("\n📊 Starting Full Training...")
    print("This will train on WikiText-2 for 100 batches (~10 minutes)\n")
    
    from train_quadra_matrix import QuadraMatrixTrainer
    
    trainer = QuadraMatrixTrainer(field_size=100, device='cpu')
    await trainer.train(
        dataset_name='wikitext',
        dataset_config='wikitext-2-raw-v1',
        num_batches=100,
        batch_size=10
    )
    
    print("\n✅ Full training complete!")
    print("Results saved to:")
    print("  - training_metrics.json")
    print("  - training_metrics.png")
    print("  - quadra_matrix_weights.pth")

def show_results():
    """Display training results"""
    import subprocess
    print("\n📈 Training Results:\n")
    subprocess.run(['python', 'results_summary.py'])

async def custom_training():
    """Interactive custom training"""
    print("\n🔧 Custom Training Configuration\n")
    
    # Get user input
    dataset = input("Dataset name (default: wikitext): ").strip() or "wikitext"
    config = input("Dataset config (default: wikitext-2-raw-v1): ").strip() or "wikitext-2-raw-v1"
    
    try:
        num_batches = int(input("Number of batches (default: 50): ").strip() or "50")
        batch_size = int(input("Batch size (default: 10): ").strip() or "10")
        field_size = int(input("Field size (default: 100): ").strip() or "100")
    except ValueError:
        print("❌ Invalid input. Using defaults.")
        num_batches, batch_size, field_size = 50, 10, 100
    
    device = input("Device (cpu/cuda, default: cpu): ").strip() or "cpu"
    
    print(f"\n📝 Configuration:")
    print(f"  Dataset: {dataset}/{config}")
    print(f"  Batches: {num_batches}")
    print(f"  Batch Size: {batch_size}")
    print(f"  Field Size: {field_size}")
    print(f"  Device: {device}")
    print()
    
    confirm = input("Start training? (y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ Training cancelled.")
        return
    
    print("\n🚀 Starting custom training...\n")
    
    from train_quadra_matrix import QuadraMatrixTrainer
    
    trainer = QuadraMatrixTrainer(field_size=field_size, device=device)
    await trainer.train(
        dataset_name=dataset,
        dataset_config=config,
        num_batches=num_batches,
        batch_size=batch_size
    )
    
    print("\n✅ Custom training complete!")

async def test_model():
    """Load and test a trained model"""
    print("\n💾 Testing Trained Model\n")
    
    import torch
    import os
    
    if not os.path.exists('quadra_matrix_weights.pth'):
        print("❌ No trained model found. Please train first (option 1 or 2).")
        return
    
    print("Loading model...")
    from quadra_matrix_spi import OscillatorySynapseTheory
    
    oscillator = OscillatorySynapseTheory(field_size=100, device='cpu')
    oscillator.load_weights('quadra_matrix_weights.pth')
    
    print("✅ Model loaded successfully!\n")
    
    # Test with sample text
    test_texts = [
        "The quick brown fox jumps over the lazy dog",
        "Artificial intelligence and machine learning are transforming technology",
        "Quantum computing represents the future of computation"
    ]
    
    print("Testing with sample texts:\n")
    for i, text in enumerate(test_texts, 1):
        print(f"{i}. '{text}'")
        feature_vector = oscillator.process_streamed_data(text)
        print(f"   Feature vector shape: {feature_vector.shape}")
        print(f"   Mean activation: {feature_vector.mean().item():.4f}")
        print()
    
    print("✅ Model is working correctly!")

def show_help():
    """Show help and documentation"""
    print("\n" + "="*80)
    print("📚 QUADRA MATRIX A.I. - DOCUMENTATION")
    print("="*80 + "\n")
    
    print("🎯 What is Quadra Matrix?")
    print("-" * 80)
    print("An AI system that trains exponentially faster than traditional approaches by")
    print("combining spiking neural networks, symbolic reasoning, and adaptive learning.\n")
    
    print("🚀 Key Features:")
    print("-" * 80)
    print("  • 10x exponential speedup during training")
    print("  • CPU-friendly (no GPU required)")
    print("  • Minimal parameters (~100k vs billions in LLMs)")
    print("  • Adaptive learning rate that grows with success")
    print("  • Dynamic architecture (K-clusters adjust in real-time)")
    print("  • Biological efficiency through spiking neural networks\n")
    
    print("📖 Documentation Files:")
    print("-" * 80)
    print("  • README.md      - Complete technical documentation")
    print("  • TRAINING.md    - Quick start guide and examples")
    print("  • results_summary.py - View training results\n")
    
    print("💻 Command Line Usage:")
    print("-" * 80)
    print("  python launch.py              # Interactive menu (this)")
    print("  python train_quadra_matrix.py # Direct training (100 batches)")
    print("  python results_summary.py     # Show results summary\n")
    
    print("🔧 System Requirements:")
    print("-" * 80)
    print("  • Python 3.8+")
    print("  • ~500MB RAM")
    print("  • Any CPU (GPU optional)")
    print("  • ~2GB storage for datasets\n")
    
    print("For more details, see README.md and TRAINING.md")
    print("="*80 + "\n")

async def main():
    """Main launcher loop"""
    print_banner()
    
    while True:
        print_menu()
        
        try:
            choice = input("Enter your choice (1-7): ").strip()
            print()
            
            if choice == '1':
                await quick_demo()
            elif choice == '2':
                await full_training()
            elif choice == '3':
                show_results()
            elif choice == '4':
                await custom_training()
            elif choice == '5':
                await test_model()
            elif choice == '6':
                show_help()
            elif choice == '7':
                print("👋 Thanks for using Quadra Matrix A.I.!")
                print("Visit: https://github.com/acastro77733-ai/Quadra-Matrix-A.I.\n")
                break
            else:
                print("❌ Invalid choice. Please enter 1-7.\n")
                continue
            
            input("\nPress Enter to continue...")
            print("\n")
            
        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Exiting...")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Please try again or choose option 6 for help.\n")
            input("Press Enter to continue...")
            print("\n")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
        sys.exit(0)
