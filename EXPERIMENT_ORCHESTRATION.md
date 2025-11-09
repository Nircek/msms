# Experiment Orchestration Guide

## Overview

The Experiment Orchestrator (Step Runner) allows you to automate procedural experiments by defining a sequence of steps that execute automatically. Each step can wait for conditions, set device parameters, or control the experiment flow.

## Features

- **Automated Execution**: Define a sequence of steps that run automatically
- **Real-Time Monitoring**: View current and next steps in the main window
- **Dynamic Modification**: Add, remove, or reorder future steps while experiment is running
- **Manual Control**: Skip to next step or stop experiment at any time
- **Data Logging**: Experiment steps and timestamps are logged in exported CSV files

## Step Types

### 1. Wait for Duration
Waits for a specified number of seconds before proceeding to the next step.

**Example**: Wait 60 seconds for system stabilization
- Duration: `60.0` seconds

### 2. Wait for Datetime
Waits until a specific date/time is reached (UTC timezone).

**Example**: Wait until midnight to start next phase
- Datetime: `2024-01-15T00:00:00+00:00` (ISO 8601 format)

### 3. Wait for Condition
Waits until a measured data column meets a threshold condition.
Checks the last 3 measurements to account for noise - all 3 must meet the condition.

**Example**: Wait for control temperature to stabilize at 300K
- Column: `control`
- Threshold: `300.0`
- Comparison: `>=` (options: `>=` or `<=`)

### 4. Set Setpoint
Sends a SETP command to a LakeShore device (non-blocking).

**Example**: Set temperature controller to 350K
- Device address: `GPIB0::10::INSTR`
- Setpoint value: `350.0`

### 5. Stop Program
Signals the end of the experiment and stops execution.

**Example**: Final step to end experiment gracefully

## Using the Experiment Manager

### Opening the Dialog

1. Launch the application
2. **IMPORTANT**: First select devices via **File → Select Devices**
3. Then select **Experiment → Manage Experiment** from the menu
4. The Experiment Plan dialog opens

### Creating an Experiment Plan

1. Click **Add Step** button
2. Select step type from dropdown (dynamically populated from registered steps)
3. Enter parameters in the dialog that appears (each step type has its own dialog)
4. **Steps are immediately sent to the experiment manager** - no need to click OK
5. Use **Move Up** / **Move Down** to reorder steps (also updates manager immediately)
6. Use **Remove Step** to delete a step (also updates manager immediately)

### Running the Experiment

1. Ensure data acquisition is started (Actions → Do...)
2. Ensure devices are selected
3. In Experiment Plan dialog, click **Start Experiment**
4. Watch the main window's experiment status panel:
   - **CURRENT**: Shows the currently executing step
   - **NEXT**: Shows the next step in the queue

### Runtime Controls

- **Skip to Next**: Immediately advance to the next step (skips current step's condition)
- **Stop Experiment**: Halt experiment execution (can be restarted later)

### Modifying During Execution

You can modify future steps while an experiment is running:
- Steps before current index: Cannot be modified (already executed)
- Current step: Cannot be removed or modified (in progress)
- Future steps: Can be added, removed, or reordered

**Note**: All modifications are immediately synchronized with the experiment manager.

## Example Experiment Plan

### Temperature Ramp Experiment

Goal: Gradually increase temperature and measure properties at each plateau.

Steps:
1. **Set Setpoint** - Set initial temperature to 250K
2. **Wait for Condition** - Wait for control >= 249K (last 3 measurements)
3. **Wait for Duration** - Wait 300s for equilibration
4. **Set Setpoint** - Increase to 300K
5. **Wait for Condition** - Wait for control >= 299K
6. **Wait for Duration** - Wait 300s for equilibration
7. **Set Setpoint** - Increase to 350K
8. **Wait for Condition** - Wait for control >= 349K
9. **Wait for Duration** - Wait 300s for equilibration
10. **Stop Program** - End experiment

### Overnight Automated Run

Goal: Start experiment at specific time and run for exact duration.

Steps:
1. **Wait for Datetime** - Wait until 2024-01-15T20:00:00+00:00 (8 PM)
2. **Set Setpoint** - Begin measurement at 300K
3. **Wait for Duration** - Run for 28800s (8 hours)
4. **Stop Program** - End experiment

## Exported Data

When you export data to CSV (Actions → Export Data), the experiment log is included as comments:

```csv
# My temperature ramp experiment
# Room 204, Dewar 3
#
# Experiment Log:
# step_1: Set GPIB0::10::INSTR: SETP 250.0 (started: 2024-01-15T14:30:00.123456+00:00)
# step_2: Wait for control >= 249.0 (started: 2024-01-15T14:30:00.456789+00:00)
# step_3: Wait for 300.0s (started: 2024-01-15T14:32:15.678901+00:00)
# step_4: Set GPIB0::10::INSTR: SETP 300.0 (started: 2024-01-15T14:37:15.890123+00:00)
...
timestamp,control,voltage,current
1705329000.123,249.1,1.234,0.001
1705329001.234,249.3,1.235,0.001
...
```

## Tips and Best Practices

### Stabilization Time
Always include **Wait for Duration** steps after setting setpoints to allow the system to reach equilibrium before taking critical measurements.

### Threshold Margins
When using **Wait for Condition**, use small margins from target values (e.g., wait for 299K instead of 300K) to account for overshoot and noise. The step checks the last 3 measurements, so all 3 must meet the condition.

### Error Recovery
If a step fails to complete (e.g., temperature never reaches threshold), use the **Skip to Next** button to manually advance. Review logs to understand why the condition wasn't met.

### Testing Plans
Before running overnight experiments:
1. Test with short durations (10s instead of 300s)
2. Verify all device commands work correctly
3. Check that conditions trigger as expected

### Device Commands
Set Setpoint steps automatically use the SETP command for LakeShore devices. Example:
- Setpoint value: 300 → Command sent: `SETP 300.0`

## Troubleshooting

### Step Never Completes
- **Wait for Condition**: Check that the column name matches exactly (case-sensitive) - use `control` not `temperature`
- **Wait for Condition**: Remember that last 3 measurements must all meet condition
- **Wait for Condition**: Verify threshold is reachable given current system state
- **Wait for Datetime**: Ensure datetime is in future and timezone is UTC

### Device Command Not Working
- Verify device is a LakeShore device (Set Setpoint only works with LakeShore)
- Check device connection and communication
- Ensure devices were selected before opening experiment dialog

### Experiment Stops Unexpectedly
- Review logs for error messages
- Check that acquisition is still running
- Verify no manual interruption occurred
- If acquisition stops, experiment will also stop automatically

## Architecture Notes

For developers extending the system:

### Adding New Step Types

1. Create new file in `msms/ui/experiment/steps/my_step.py`:
```python
from msms.ui.experiment.register_step import register_step
from msms.ui.experiment.step_base import Step

@register_step("My Custom Step")
class MyCustomStep(Step):
    def __init__(self, step_id: str, param1: str) -> None:
        super().__init__(step_id, f"My Step: {param1}")
        self.param1 = param1

    @classmethod
    def create_config_dialog(cls, _parent: QtWidgets.QWidget | None) -> QtWidgets.QDialog | None:
        # Return dialog or None to use QInputDialog
        return None

    @classmethod
    def create_from_dialog(cls, _dialog: QtWidgets.QDialog | None, step_id: str) -> Step | None:
        # Get parameters from user
        param1, ok = QtWidgets.QInputDialog.getText(_dialog, "Config", "Parameter:")
        if ok:
            return cls(step_id, param1)
        return None

    def evaluate(self, _runner: ExperimentManager) -> bool:
        # Return True when step is complete
        return my_condition_met()
```

2. Import in `msms/ui/experiment/steps/__init__.py` to trigger registration
3. Step will automatically appear in the "Add Step" dropdown

### Step Registration

Steps use a decorator-based registration system (similar to device registration):
- `@register_step(display_name)` decorator auto-registers the step class
- `step_registry` global list contains all registered steps
- Registration happens at import time

### Thread Safety

The ExperimentManager runs in a separate thread. All communication must use Qt signals/slots:
- **Never** set ExperimentManager parent (violates Qt threading rules)
- Steps send device commands via `runner.send_device_command()` which emits a signal
- Dialog modifications immediately emit signals to update manager state

### Signal Flow

```
User adds step in dialog
    ↓
ExperimentDialog._add_step()
    ↓
ApplicationController.set_experiment_steps()
    ↓
experiment_set_steps_requested signal
    ↓
ExperimentManager.on_set_steps() [Worker Thread]
    ↓
Steps stored in manager._steps
```

```
User clicks Start
    ↓
ExperimentDialog._start_experiment()
    ↓
ApplicationController.start_experiment()
    ↓
experiment_start_requested signal
    ↓
ExperimentManager.on_start_request() [Worker Thread]
    ↓
Timer triggers _evaluate_step() every 1s
    ↓
current_step_changed signal
    ↓
MainWindow updates experimentPlanTextEdit
```

### Device Command Flow

```
Step.on_start() or Step.evaluate()
    ↓
runner.send_device_command(address, command)
    ↓
ExperimentManager.device_command_requested signal
    ↓
ApplicationController.device_command_requested signal
    ↓
DeviceManager.on_device_command_request()
    ↓
Command sent to device
```

## Support

For questions or issues:
1. Check logs in `logs/` directory
2. Review step definitions in experiment dialog
3. Verify device connections and acquisition state
4. Ensure devices were selected before opening experiment dialog
