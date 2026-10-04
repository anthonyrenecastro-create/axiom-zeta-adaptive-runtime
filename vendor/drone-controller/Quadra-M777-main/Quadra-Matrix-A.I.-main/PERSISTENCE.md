# QuadraMatrix A.I. - Persistent Memory System

## Overview

The dashboard now includes **automatic persistent memory** that saves your training progress to disk, allowing you to resume training across sessions.

## 🔄 What Gets Saved

### Neural Network Weights
- All 3 spiking neural networks (Field Update, Syntropy, Feedback)
- Q-learning table with state-action values
- Field state tensors

### Training Metrics
- Complete loss history
- Complete reward history  
- Field variance history
- Field mean history
- Total iteration count

### System State
- Field size configuration
- Initialization status
- Integrity strikes count
- Neuroplasticity manager state

## 💾 Storage Location

All state is saved in the `dashboard_state/` directory:

```
dashboard_state/
├── oscillator_weights.pth      # PyTorch neural network weights
├── metrics_history.pkl         # Training metrics (pickle)
└── system_state.pkl           # System configuration (pickle)
```

## 🚀 How to Use

### Auto-Save (Automatic)
The system **automatically saves** your progress:
- **Every 10 iterations** during training
- **When you click "Stop Training"**

You don't need to do anything - it just works! ✨

### Load Saved State
1. Click **"Load Saved State"** button (pink gradient)
2. System restores:
   - All neural network weights
   - Complete training history
   - All charts with historical data
   - Exact iteration count
3. Click **"Start Training"** to continue where you left off

### Fresh Start
1. Click **"Initialize System"** for a brand new training session
2. This creates new networks from scratch

### Complete Reset
1. Click **"Reset System"**
2. Confirms deletion of saved state
3. Completely clears all data from memory AND disk

## 📊 Benefits

### 1. Resume Training Anytime
```
Session 1: Train 100 iterations → Log out
Session 2: Load state → Continue from iteration 101
```

### 2. Experiment Safely
- Save a good state
- Try new configurations
- Load back if needed

### 3. Long-term Learning
- Build up Q-table knowledge over days/weeks
- Networks continue improving across sessions
- Track progress over time

### 4. No Data Loss
- Server crash? State saved every 10 iterations
- Accidentally closed browser? Just reload and continue
- Power outage? Last auto-save has you covered

## 🎯 Example Workflow

```bash
# Day 1: Initial training
1. Click "Initialize System"
2. Click "Start Training"
3. Let it run to 200 iterations
4. Click "Stop Training" (auto-saves)
5. Close browser

# Day 2: Continue training
1. Open dashboard
2. Click "Load Saved State"
3. See all 200 iterations restored in charts
4. Click "Start Training" to continue from 201
5. Train to 500 iterations
6. Click "Stop Training" (auto-saves)

# Day 3: Experiment with fresh start
1. Click "Initialize System" (new training)
2. Train 100 iterations
3. Not happy? Close without saving
4. Click "Load Saved State" (back to 500 iterations)
```

## 🔧 Technical Details

### Save Format
- **PyTorch format (.pth)**: For neural networks (efficient, GPU-compatible)
- **Pickle format (.pkl)**: For metrics and configuration (Python native)

### Save Frequency
- Manual: Stop button
- Automatic: Every 10th iteration
- Configurable in code: `if state.iteration_count % 10 == 0`

### Performance Impact
- Save operation: ~100-500ms (non-blocking)
- Load operation: ~200-800ms (one-time startup)
- No impact on training speed

### File Sizes
Typical storage requirements:
- `oscillator_weights.pth`: ~500 KB - 2 MB
- `metrics_history.pkl`: ~10 KB per 1000 iterations
- `system_state.pkl`: ~1 KB

## 🛡️ Safety Features

### Atomic Saves
- Files written completely before overwriting
- No partial/corrupted saves

### Error Handling
- Failed saves don't crash training
- Failed loads fall back to initialization
- Clear error messages in logs

### Data Validation
- State compatibility checks
- Version mismatch detection
- Graceful degradation

## 📝 Logging

Watch the terminal output for save/load confirmations:

```
✓ State saved: 100 iterations
✓ State saved: 110 iterations
...
✓ State loaded: 220 iterations restored
```

## 🔍 Advanced Usage

### Manual Save Frequency
Edit `app.py` line ~290:
```python
# Save every 10 iterations (default)
if state.iteration_count % 10 == 0:
    state.save_state()

# Save every 50 iterations (slower disk I/O)
if state.iteration_count % 50 == 0:
    state.save_state()

# Save every iteration (maximum safety)
state.save_state()
```

### Custom Storage Location
Edit `app.py` line ~18:
```python
STATE_DIR = 'dashboard_state'  # Default
STATE_DIR = '/path/to/backup'  # Custom location
STATE_DIR = os.path.expanduser('~/quadra_state')  # User home
```

### Backup Important States
```bash
# Create backup of great training run
cp -r dashboard_state dashboard_state_backup_500iter

# Restore from backup
rm -rf dashboard_state
cp -r dashboard_state_backup_500iter dashboard_state
```

## 🚨 Troubleshooting

### "No saved state found"
- **Cause**: First time running, or state was reset
- **Solution**: Click "Initialize System" to start fresh

### "Failed to load state"
- **Cause**: Corrupted file or incompatible version
- **Solution**: Delete `dashboard_state/` and start fresh

### Charts don't update after load
- **Cause**: Browser cache issue
- **Solution**: Hard refresh (Ctrl+Shift+R) or clear browser cache

### State not saving
- **Cause**: Disk full or permission issues
- **Solution**: Check terminal logs for error details

## 💡 Tips & Tricks

1. **Checkpoint Important Milestones**: After achieving good results, backup the `dashboard_state/` folder

2. **Compare Training Runs**: Copy state to different folders to A/B test configurations

3. **Cloud Sync**: Put `dashboard_state/` in Dropbox/Google Drive for cross-machine training

4. **Version Control**: `.gitignore` the state folder or commit it to track progress

5. **Monitor Terminal**: Watch for "✓ State saved" messages to confirm auto-saves

## 🎓 Best Practices

✅ **DO:**
- Let auto-save handle routine saves
- Use "Stop Training" before closing
- Load state to continue long training runs
- Backup `dashboard_state/` before experiments

❌ **DON'T:**
- Kill the process during training (may lose last 10 iterations)
- Manually edit .pth or .pkl files
- Share state files between different system architectures
- Ignore "Failed to save" errors

## 📈 Future Enhancements

Potential additions:
- [ ] Multiple save slots (Save Slot 1, 2, 3)
- [ ] Cloud backup integration
- [ ] State comparison tools
- [ ] Export training reports
- [ ] Rollback to previous iterations
- [ ] Automatic best-state detection

## 🤝 Integration

The persistence system integrates seamlessly with:
- All training algorithms
- Q-learning table updates
- Field dynamics
- Syntropy regulation
- Pattern recognition
- Neural network evolution

No configuration needed - it just works! 🎉

---

**Memory that lasts. Training that persists. Progress that never ends.** 🚀
