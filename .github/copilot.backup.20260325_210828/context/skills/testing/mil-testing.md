# Skill: Model-in-the-Loop (MIL) Testing for Automotive Control Systems

## When to Activate
- User is developing control algorithms in MATLAB/Simulink for automotive ECUs
- User needs to validate algorithms against requirements before code generation
- User requests model coverage analysis (decision, condition, MC/DC)
- User is designing test harnesses for Simulink models
- User needs back-to-back testing strategy (MIL→SIL→PIL→HIL)
- User requests plant model development for powertrain, battery, or vehicle dynamics
- User needs automated MIL test execution and reporting

## Standards Compliance
- **ISO 26262-6:2018** (Software Testing) - MIL as early verification method
- **ASPICE Level 3** - SWE.3 (Detailed Design), SWE.4 (Unit Testing)
- **AUTOSAR 4.4** - Model-based development workflow
- **MISRA C:2012** - Code generation target compliance
- **IEC 61508** - Model-based development for safety systems
- **DO-178C/DO-331** - Model-based development (aerospace reference)

## Key Parameters
| Parameter | Range/Options | Unit |
|-----------|---------------|------|
| Model step size | 0.001-1 | s |
| Simulation duration | Seconds-hours | time |
| Number of test cases | 10-10000+ | count |
| Model coverage target | 95-100 | % |
| Back-to-back tolerance | 0.01-1 | % |
| Test execution time | Minutes-hours | duration |
| Plant model fidelity | Low/Medium/High | enumeration |
| Solver type | Fixed-step/Variable-step | enumeration |

## MIL Testing Architecture

```
+-----------------------------------------------------------------------+
|                    MIL Test Environment                                |
|                                                                       |
|  +---------------------------+        +---------------------------+   |
|  |  Controller Model         |        |  Plant Model              |   |
|  |  (Simulink/Stateflow)     |        |  (Simulink)               |   |
|  |                           |        |                           |   |
|  |  +---------------------+  |        |  +---------------------+  |   |
|  |  | Control Algorithm   |  |        |  | Engine/Battery/     |  |   |
|  |  | (PID, State Machine,|  |        |  | Vehicle Dynamics    |  |   |
|  |  |  Observer, etc.)    |  |        |  |                     |  |   |
|  |  +---------------------+  |        |  +---------------------+  |   |
|  |            |              |        |            |              |   |
|  |  +---------------------+  |        |  +---------------------+  |   |
|  |  | Test Harness        |<-+--------+->|  | Environment        |  |   |
|  |  | - Test Sequences    |  | Inputs |  |  | - Driver Model     |  |   |
|  |  | - Stimulus Signals  |  | Outputs|  |  | - Road Profile     |  |   |
|  |  | - Measurement       |  |        |  |  | - Ambient Conditions||  |
|  |  +---------------------+  |        |  +---------------------+  |   |
|  +---------------------------+        +---------------------------+   |
|           |                                        |                   |
|           v                                        v                   |
|  +------------------+                    +------------------+          |
|  | Test Automation  |                    | Coverage Analysis|          |
|  | - Simulink Test  |                    | - Model Coverage |          |
|  | - MATLAB scripts |                    | - Decision       |          |
|  | - Test Manager   |                    | - Condition      |          |
|  |                  |                    | - MC/DC          |          |
|  +------------------+                    +------------------+          |
+-----------------------------------------------------------------------+
```

## MATLAB/Simulink Test Framework

### Test Harness Design

```matlab
% Simulink test harness for BMS SOC estimation algorithm
function create_bms_soc_test_harness()
    % Create new model
    model_name = 'bms_soc_test_harness';
    new_system(model_name);
    open_system(model_name);

    % Add Controller (System Under Test)
    add_block('bms_soc_estimator/Algorithm', ...
        [model_name '/SOC_Estimator'], ...
        'Position', [200 100 350 200]);

    % Add Plant Model (Battery)
    add_block('battery_models/Lithium_Ion_ECM', ...
        [model_name '/Battery_Plant'], ...
        'Position', [450 100 600 200]);

    % Add Test Sequence Generator
    add_block('simulink/Sources/Signal Builder', ...
        [model_name '/Test_Sequence'], ...
        'Position', [50 100 150 200]);

    % Add Measurement Blocks
    add_block('simulink/Sinks/Scope', ...
        [model_name '/Scope_SOC'], ...
        'Position', [650 50 750 150]);
    add_block('simulink/Sinks/To Workspace', ...
        [model_name '/SOC_Data'], ...
        'Position', [650 150 750 250]);
    add_block('simulink/Sinks/Assertion', ...
        [model_name '/SOC_Range_Check'], ...
        'Position', [650 250 750 350]);

    % Connect blocks
    add_line(model_name, 'Test_Sequence/1', 'SOC_Estimator/current_a');
    add_line(model_name, 'Test_Sequence/2', 'Battery_Plant/Current');
    add_line(model_name, 'Battery_Plant/Voltage', 'SOC_Estimator/voltage_v');
    add_line(model_name, 'SOC_Estimator/soc_percent', 'Scope_SOC/1');
    add_line(model_name, 'SOC_Estimator/soc_percent', 'SOC_Data/1');
    add_line(model_name, 'SOC_Estimator/soc_percent', 'SOC_Range_Check/1');

    % Configure assertion
    set_param([model_name '/SOC_Range_Check'], ...
        'Assert', 'u1 >= 0 && u1 <= 100', ...
        'StopSimulation', 'on');

    % Save model
    save_system(model_name);
    fprintf('Test harness created: %s\n', model_name);
end
```

### Test Case Specification

```matlab
% MIL test case definition for SOC estimation
classdef SocEstimationTest < matlab.unittest.TestCase
    properties
        model_name = 'bms_soc_test_harness'
        tolerance_percent = 2.0  % SOC accuracy requirement
    end

    properties (TestClassParameter)
        test_scenario = {'constant_current_discharge', ...
                         'dynamic_load_profile', ...
                         'rest_period_recovery', ...
                         'temperature_variation'}
    end

    methods (Test)
        function test_constant_current_discharge(test_case)
            % Scenario: Constant current discharge from 100% SOC
            test_case.setup_simulation('current_profile', -50, ...
                                       'duration_s', 3600, ...
                                       'temperature_c', 25);

            sim_output = sim(test_case.model_name);

            % Verify SOC decreases monotonically
            soc_signal = sim_output.soc_percent.Data;
            test_case.assertTrue(all(diff(soc_signal) <= 0), ...
                'SOC must decrease during discharge');

            % Verify final SOC within expected range
            expected_final_soc = 100 - (50 * 1) / 75 * 100;  % 75 Ah battery
            actual_final_soc = soc_signal(end);
            test_case.verifyLessThan(abs(actual_final_soc - expected_final_soc), ...
                test_case.tolerance_percent, ...
                'Final SOC error exceeds 2%%');
        end

        function test_dynamic_load_profile(test_case)
            % Scenario: Dynamic current profile (WLTC-derived)
            load('wltc_current_profile.mat');  % current_profile, time_vector

            test_case.setup_simulation('current_profile', current_profile, ...
                                       'time_vector', time_vector, ...
                                       'temperature_c', 25);

            sim_output = sim(test_case.model_name);

            % Verify SOC stays within bounds
            soc_signal = sim_output.soc_percent.Data;
            test_case.verifyGreaterThan(min(soc_signal), 0, ...
                'SOC must not go negative');
            test_case.verifyLessThan(max(soc_signal), 100, ...
                'SOC must not exceed 100%%');

            % Verify SOC at end of cycle (coulomb counting check)
            net_charge_ah = -trapz(current_profile) / 3600;
            expected_soc_change = net_charge_ah / 75 * 100;
            actual_soc_change = soc_signal(end) - soc_signal(1);
            test_case.verifyLessThan(abs(actual_soc_change - expected_soc_change), ...
                test_case.tolerance_percent, ...
                'SOC change exceeds coulomb counting tolerance');
        end

        function test_temperature_variation(test_case)
            % Scenario: Temperature effect on SOC estimation
            temperatures = [-10, 0, 25, 45];  % Test at multiple temperatures

            for temp = temperatures
                test_case.setup_simulation('current_profile', -20, ...
                                           'duration_s', 1800, ...
                                           'temperature_c', temp);

                sim_output = sim(test_case.model_name);
                soc_signal = sim_output.soc_percent.Data;

                % Verify temperature compensation is active
                test_case.verifyTrue(isfinite(soc_signal), ...
                    sprintf('SOC NaN at %d°C', temp));
                test_case.verifyTrue(all(soc_signal >= 0 & soc_signal <= 100), ...
                    sprintf('SOC out of range at %d°C', temp));
            end
        end
    end

    methods
        function setup_simulation(test_case, varargin)
            % Configure simulation parameters
            params = varargin;

            % Set model workspace variables
            assignin('model', test_case.model_name, 'current_profile', params.current_profile);
            if isfield(params, 'duration_s')
                set_param(test_case.model_name, 'StopTime', num2str(params.duration_s));
            end
            if isfield(params, 'temperature_c')
                assignin('model', test_case.model_name, 'ambient_temp', params.temperature_c);
            end

            % Configure solver
            set_param(test_case.model_name, 'Solver', 'FixedStepDiscrete');
            set_param(test_case.model_name, 'FixedStep', '0.001');  % 1ms
        end
    end
end
```

## Model Coverage Analysis

### Coverage Types

```matlab
% Model coverage analysis for Simulink models
function analyze_model_coverage(model_name)
    % Configure coverage collection
    cvconfig = coverage.Config;
    cvconfig.ModelName = model_name;
    cvconfig.ReportFormat = 'html';
    cvconfig.SaveWorkspace = true;

    % Coverage types for ISO 26262 compliance
    cvconfig.MeasureDecisionCoverage = true;    % Decision coverage (MDC)
    cvconfig.MeasureConditionCoverage = true;   % Condition coverage (MCC)
    cvconfig.MeasureMCDC = true;                % MC/DC for ASIL D

    % Run simulation with coverage
    sim(model_name);

    % Generate coverage report
    covdata = coverage.collect(model_name);
    coverage.report(covdata, 'Format', 'html', ...
                    'File', 'coverage_report.html');

    % Analyze coverage metrics
    decision_coverage = get_decision_coverage(covdata);
    condition_coverage = get_condition_coverage(covdata);
    mcdc_coverage = get_mcdc_coverage(covdata);

    fprintf('Model Coverage Report for %s:\n', model_name);
    fprintf('  Decision Coverage:  %.1f%%\n', decision_coverage);
    fprintf('  Condition Coverage: %.1f%%\n', condition_coverage);
    fprintf('  MC/DC Coverage:     %.1f%%\n', mcdc_coverage);

    % Identify uncovered elements
    uncovered_decisions = get_uncovered_decisions(covdata);
    uncovered_conditions = get_uncovered_conditions(covdata);

    if ~isempty(uncovered_decisions)
        fprintf('\nUncovered Decisions:\n');
        for i = 1:length(uncovered_decisions)
            fprintf('  - %s (line %d)\n', ...
                uncovered_decisions{i}.block, uncovered_decisions{i}.line);
        end
    end
end

% Coverage analysis for ASIL-based requirements
function verify_coverage_for_asil(covdata, asil_level)
    switch asil_level
        case 'A'
            % Statement coverage required
            min_coverage = 80;
            coverage_type = 'statement';
        case 'B'
            % Branch coverage required
            min_coverage = 90;
            coverage_type = 'decision';
        case 'C'
            % Branch + condition coverage required
            min_coverage = 95;
            coverage_type = 'condition';
        case 'D'
            % MC/DC coverage required
            min_coverage = 95;
            coverage_type = 'mcdc';
        otherwise
            error('Unknown ASIL level: %s', asil_level);
    end

    actual_coverage = get_coverage_metric(covdata, coverage_type);

    if actual_coverage < min_coverage
        warning('Coverage %.1f%% below %s requirement of %.1f%% for ASIL %s', ...
            actual_coverage, coverage_type, min_coverage, asil_level);
    else
        fprintf('PASS: %s coverage %.1f%% meets ASIL %s requirement\n', ...
            coverage_type, actual_coverage, asil_level);
    end
end
```

### MC/DC Coverage for Stateflow

```matlab
% MC/DC analysis for Stateflow state machines
function analyze_stateflow_mcdc(model_name)
    % Load coverage data
    covdata = coverage.collect(model_name);

    % Extract Stateflow chart coverage
    sf_blocks = find_system(model_name, 'BlockType', 'Stateflow');

    for i = 1:length(sf_blocks)
        chart = sf_blocks{i};
        fprintf('\nStateflow Chart: %s\n', chart);

        % State coverage
        state_coverage = get_state_coverage(covdata, chart);
        fprintf('  State Coverage: %.1f%%\n', state_coverage.percent);

        % Transition coverage
        trans_coverage = get_transition_coverage(covdata, chart);
        fprintf('  Transition Coverage: %.1f%%\n', trans_coverage.percent);

        % Condition coverage (for guarded transitions)
        cond_coverage = get_condition_coverage(covdata, chart);
        fprintf('  Condition Coverage: %.1f%%\n', cond_coverage.percent);

        % MC/DC for complex conditions
        if contains(chart, 'ASIL_D')
            mcdc_coverage = get_mcdc_coverage(covdata, chart);
            fprintf('  MC/DC Coverage: %.1f%%\n', mcdc_coverage.percent);

            % Verify MC/DC meets ASIL D requirement
            if mcdc_coverage.percent < 95
                fprintf('  WARNING: MC/DC below 95%% ASIL D target\n');
            end
        end
    end
end

% Test vector generation for MC/DC
function generate_mcdc_test_vectors(condition_expr)
    % Parse condition expression
    % Example: (A && B) || (C && D)

    % Extract atomic conditions
    conditions = extract_conditions(condition_expr);
    n_conditions = length(conditions);

    % Generate minimum test vectors for MC/DC
    % For n conditions, need n+1 test vectors minimum

    test_vectors = cell(n_conditions + 1, 1);

    % Base case: all false
    test_vectors{1} = struct();
    for i = 1:n_conditions
        test_vectors{1}.(conditions{i}) = false;
    end

    % Generate independence pairs
    for i = 1:n_conditions
        test_vectors{i+1} = test_vectors{1};
        test_vectors{i+1}.(conditions{i}) = true;
    end

    % Display test vectors
    fprintf('MC/DC Test Vectors for: %s\n', condition_expr);
    for i = 1:length(test_vectors)
        fprintf('  T%d: ', i);
        for j = 1:n_conditions
            fprintf('%s=%d ', conditions{j}, test_vectors{i}.(conditions{j}));
        end
        fprintf('\n');
    end
end
```

## Back-to-Back Testing

### MIL→SIL Comparison

```matlab
% Back-to-back testing: MIL vs SIL
function run_back_to_back_test()
    % Configuration
    mil_model = 'bms_soc_estimator';
    sil_model = 'bms_soc_estimator_sil';  % Generated C code wrapper

    % Test scenarios
    test_scenarios = {
        'constant_current', -50, 3600;
        'dynamic_load', 'wltc_profile', 1800;
        'temperature_sweep', -10, 600;
    };

    results = struct();

    for i = 1:size(test_scenarios, 1)
        scenario = test_scenarios{i, 1};
        fprintf('\n=== Scenario: %s ===\n', scenario);

        % Run MIL
        setup_scenario(mil_model, test_scenarios{i, 2}, test_scenarios{i, 3});
        mil_output = sim(mil_model);
        mil_soc = mil_output.soc_percent.Data;

        % Run SIL
        setup_scenario(sil_model, test_scenarios{i, 2}, test_scenarios{i, 3});
        sil_output = sim(sil_model);
        sil_soc = sil_output.soc_percent.Data;

        % Compare outputs
        time_vector = mil_output.tout;

        % Absolute error
        abs_error = abs(mil_soc - sil_soc);
        max_abs_error = max(abs_error);

        % Relative error (avoid division by zero)
        rel_error = abs_error ./ (abs(mil_soc) + 0.01) * 100;
        max_rel_error = max(rel_error);

        % Store results
        results.(scenario).max_abs_error = max_abs_error;
        results.(scenario).max_rel_error = max_rel_error;
        results.(scenario).passed = (max_rel_error < 0.1);  % 0.1% tolerance

        fprintf('  Max Absolute Error: %.6f%%\n', max_abs_error);
        fprintf('  Max Relative Error: %.4f%%\n', max_rel_error);
        fprintf('  Status: %s\n', ...
            ternary(results.(scenario).passed, 'PASS', 'FAIL'));
    end

    % Generate comparison report
    generate_back_to_back_report(results, mil_output, sil_output);
end

function generate_back_to_back_report(results, mil_output, sil_output)
    % Create comparison plots
    figure('Position', [100 100 1200 800]);

    % Plot 1: SOC comparison
    subplot(2, 2, 1);
    plot(mil_output.tout, mil_output.soc_percent.Data, 'b-', ...
         sil_output.tout, sil_output.soc_percent.Data, 'r--');
    legend('MIL', 'SIL');
    xlabel('Time (s)');
    ylabel('SOC (%)');
    title('SOC Comparison: MIL vs SIL');
    grid on;

    % Plot 2: Error over time
    subplot(2, 2, 2);
    error = mil_output.soc_percent.Data - sil_output.soc_percent.Data;
    plot(mil_output.tout, error, 'k-');
    xlabel('Time (s)');
    ylabel('Error (%)');
    title('SOC Error: MIL - SIL');
    grid on;

    % Plot 3: Error histogram
    subplot(2, 2, 3);
    histogram(error, 50);
    xlabel('Error (%)');
    ylabel('Frequency');
    title('Error Distribution');
    grid on;

    % Plot 4: Summary statistics
    subplot(2, 2, 4);
    axis off;
    stats_text = {
        sprintf('Mean Error: %.6f%%', mean(error)),
        sprintf('Max Error: %.6f%%', max(abs(error))),
        sprintf('Std Dev: %.6f%%', std(error)),
        sprintf('RMSE: %.6f%%', sqrt(mean(error.^2)))
    };
    text(0.1, 0.8, stats_text, 'FontSize', 12, 'FontName', 'monospace');

    % Save figure
    saveas(gcf, 'back_to_back_comparison.png');
end
```

### SIL→PIL Comparison

```matlab
% SIL to PIL back-to-back testing
function run_sil_pil_comparison()
    % Target processor configuration
    target = 'Infineon TC397';
    compiler = 'TASKING TriCore';

    % Build PIL executable
    pil_config = coder.TargetConfig;
    pil_config.Target = target;
    pil_config.Compiler = compiler;
    pil_config.Optimization = '-O2';
    pil_config.FloatingPoint = 'single';

    build_pil_executable('bms_soc_estimator', pil_config);

    % Configure PIL block in Simulink
    set_param('bms_soc_estimator_pil/SOC_Estimator', ...
        'BlockType', 'S-Function', ...
        'SFunctionName', 'pil_block', ...
        'Executable', 'bms_soc_estimator_pil.exe');

    % Run SIL
    setup_scenario('bms_soc_estimator_sil', -50, 3600);
    sil_output = sim('bms_soc_estimator_sil');

    % Run PIL
    setup_scenario('bms_soc_estimator_pil', -50, 3600);
    pil_output = sim('bms_soc_estimator_pil');

    % Compare SIL vs PIL
    soc_sil = sil_output.soc_percent.Data;
    soc_pil = pil_output.soc_percent.Data;

    % Quantization error (fixed-point effects)
    soc_error = soc_sil - soc_pil;

    fprintf('SIL vs PIL Comparison:\n');
    fprintf('  Mean Error: %.6f%%\n', mean(soc_error));
    fprintf('  Max Error: %.6f%%\n', max(abs(soc_error)));

    % Verify within acceptable tolerance
    if max(abs(soc_error)) < 0.5
        fprintf('  Status: PASS (within 0.5%% tolerance)\n');
    else
        fprintf('  Status: FAIL (exceeds 0.5%% tolerance)\n');
    end
end
```

## Test Vector Generation

### Automated Test Generation

```matlab
% Automated test vector generation from requirements
function test_vectors = generate_test_vectors(requirements)
    % Parse requirements and extract test conditions
    test_vectors = {};

    for i = 1:length(requirements)
        req = requirements{i};

        % Extract input ranges from requirement
        input_specs = parse_input_specifications(req);

        % Generate test vectors using equivalence partitioning
        eq_test_vectors = generate_equivalence_classes(input_specs);

        % Generate test vectors using boundary value analysis
        boundary_test_vectors = generate_boundary_values(input_specs);

        % Combine and deduplicate
        combined = [eq_test_vectors; boundary_test_vectors];
        test_vectors = [test_vectors; combined];

        % Tag with requirement ID
        for j = 1:length(combined)
            test_vectors{end}.requirement_id = req.id;
            test_vectors{end}.asil = req.asil;
        end
    end

    fprintf('Generated %d test vectors from %d requirements\n', ...
        length(test_vectors), length(requirements));
end

function eq_vectors = generate_equivalence_classes(input_specs)
    % Generate equivalence class test vectors
    eq_vectors = {};

    for field = fieldnames(input_specs)'
        spec = input_specs.(field{1});

        % Valid equivalence class (within range)
        valid_value = (spec.min + spec.max) / 2;
        eq_vectors{end+1} = create_test_vector(field{1}, valid_value);

        % Invalid equivalence classes (outside range)
        if spec.min > -inf
            eq_vectors{end+1} = create_test_vector(field{1}, spec.min - spec.step);
        end
        if spec.max < inf
            eq_vectors{end+1} = create_test_vector(field{1}, spec.max + spec.step);
        end
    end
end

function boundary_vectors = generate_boundary_values(input_specs)
    % Generate boundary value test vectors
    boundary_vectors = {};

    for field = fieldnames(input_specs)'
        spec = input_specs.(field{1});

        % Minimum boundary
        boundary_vectors{end+1} = create_test_vector(field{1}, spec.min);
        boundary_vectors{end+1} = create_test_vector(field{1}, spec.min + spec.step);

        % Maximum boundary
        boundary_vectors{end+1} = create_test_vector(field{1}, spec.max);
        boundary_vectors{end+1} = create_test_vector(field{1}, spec.max - spec.step);

        % Nominal (middle)
        boundary_vectors{end+1} = create_test_vector(field{1}, (spec.min + spec.max) / 2);
    end
end
```

### Test Sequence Builder

```matlab
% Build comprehensive test sequences
function build_test_sequences()
    % Test scenario: Complete BMS validation
    test_sequence = TestSequence('BMS_Comprehensive_Validation');

    % Phase 1: Initialization
    test_sequence.add_segment('initialization', ...
        'duration', 10, ...
        'current', 0, ...
        'temperature', 25, ...
        'expected_soc', 100);

    % Phase 2: Constant current discharge
    test_sequence.add_segment('cc_discharge', ...
        'duration', 1800, ...
        'current', -50, ...
        'temperature', 25, ...
        'expected_soc_end', 67);  % 50A * 0.5h / 75Ah = 33% discharged

    % Phase 3: Rest period
    test_sequence.add_segment('rest', ...
        'duration', 600, ...
        'current', 0, ...
        'temperature', 25, ...
        'expected_soc_end', 67);  % SOC should stabilize

    % Phase 4: Charge
    test_sequence.add_segment('charge', ...
        'duration', 1200, ...
        'current', 30, ...
        'temperature', 25, ...
        'expected_soc_end', 95);

    % Phase 5: Dynamic load
    test_sequence.add_segment('dynamic', ...
        'duration', 3600, ...
        'current_profile', 'wltc', ...
        'temperature', 25);

    % Phase 6: Temperature variation
    test_sequence.add_segment('temp_sweep', ...
        'duration', 1800, ...
        'current', -20, ...
        'temperature_profile', [-10, 0, 25, 45]);

    % Save test sequence
    test_sequence.save('test_sequences/bms_comprehensive.mat');

    % Export to Simulink Signal Builder format
    test_sequence.export_to_signal_builder('bms_soc_test_harness');
end
```

## Test Automation and Reporting

### MATLAB Test Manager Integration

```matlab
% Automated test execution with MATLAB Test Manager
function run_automated_mil_tests()
    % Create test suite
    suite = testsuite('mil_tests');

    % Configure test run
    opts = test.run;
    opts.OutputDetails = 'terse';
    opts.Verbose = false;
    opts.StopOnError = false;
    opts.Parallel = true;

    % Run tests
    results = run(opts, suite);

    % Generate JUnit XML report (for CI/CD integration)
    junitResult = toJUnitXml(results);
    writetext(junitResult, 'test_results/mil_junit.xml');

    % Generate HTML report
    toHtml(results, 'test_results/mil_report.html');

    % Display summary
    fprintf('\n=== MIL Test Summary ===\n');
    fprintf('Total: %d tests\n', results.Total);
    fprintf('Passed: %d (%.1f%%)\n', results.Passed, ...
        results.Passed/results.Total*100);
    fprintf('Failed: %d\n', results.Failed);
    fprintf('Duration: %.1f seconds\n', results.Duration);

    % Check for failures
    if results.Failed > 0
        fprintf('\nFailed Tests:\n');
        failed_tests = results.selectFailed;
        for i = 1:length(failed_tests)
            fprintf('  - %s: %s\n', ...
                failed_tests(i).Name, failed_tests(i).FailureDetails.Message);
        end
    end

    % Check coverage
    if results.Passed == results.Total
        fprintf('\nAll tests passed. Generating coverage report...\n');
        analyze_model_coverage('bms_soc_test_harness');
    end
end
```

### CI/CD Integration

```yaml
# GitHub Actions workflow for MIL testing
name: MIL Test Automation

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop]

jobs:
  mil-testing:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        matlab-version: ['R2024a', 'R2024b']

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up MATLAB
        uses: matlab-actions/setup-matlab@v2
        with:
          release: ${{ matrix.matlab-version }}
          products: Simulink Stateflow Simulink_Test Coverage

      - name: Run MIL Tests
        uses: matlab-actions/run-command@v2
        with:
          command: |
            addpath('models');
            addpath('test');
            run_automated_mil_tests();

      - name: Upload Test Results
        uses: actions/upload-artifact@v4
        with:
          name: mil-test-results-${{ matrix.matlab-version }}
          path: test_results/

      - name: Check Coverage
        uses: matlab-actions/run-command@v2
        with:
          command: |
            covdata = coverage.collect('bms_soc_test_harness');
            mcdc = get_mcdc_coverage(covdata);
            if mcdc.percent < 95
              error('MC/DC coverage %.1f%% below 95%% requirement', mcdc.percent);
            end

      - name: Generate Coverage Badge
        uses: matlab-actions/run-command@v2
        with:
          command: |
            covdata = coverage.collect('bms_soc_test_harness');
            coverage.report(covdata, 'Format', 'badge', ...
                           'File', 'coverage_badge.svg');

      - name: Upload Coverage Badge
        uses: actions/upload-artifact@v4
        with:
          name: coverage-badge
          path: coverage_badge.svg
```

## Approach

1. **Define test objectives**
   - Identify requirements to verify through MIL testing
   - Determine coverage targets (statement, decision, MC/DC)
   - Define back-to-back tolerance thresholds

2. **Develop test harness**
   - Create Simulink test harness for System Under Test (SUT)
   - Integrate plant model (engine, battery, vehicle)
   - Add measurement and assertion blocks

3. **Generate test vectors**
   - Extract test conditions from requirements
   - Apply equivalence partitioning and boundary value analysis
   - Generate test sequences for each scenario

4. **Execute tests**
   - Run automated test suite via MATLAB Test Manager
   - Collect coverage data during simulation
   - Capture failures and log results

5. **Analyze coverage**
   - Measure decision, condition, and MC/DC coverage
   - Identify uncovered model elements
   - Add test cases to improve coverage

6. **Back-to-back comparison**
   - Compare MIL results with SIL (generated code)
   - Verify numerical consistency within tolerance
   - Document any discrepancies

7. **Generate reports**
   - Produce test summary with pass/fail statistics
   - Create coverage report with uncovered elements
   - Export results for traceability (DOORS, Polarion)

## Deliverables

- **Test Harness Model** - Simulink test harness with SUT and plant model
- **Test Sequence Library** - Reusable test scenarios and profiles
- **Coverage Report** - Model coverage analysis (decision, condition, MC/DC)
- **Test Results** - Pass/fail status with requirement traceability
- **Back-to-Back Report** - MIL vs SIL comparison with error analysis
- **Automated Test Scripts** - MATLAB test functions and Test Manager suite
- **CI/CD Integration** - GitHub Actions/Jenkins pipeline configuration

## Related Context

- [@context/skills/testing/sil-testing.md](../testing/sil-testing.md) - Software-in-the-Loop testing
- [@context/skills/testing/hil-testing.md](../testing/hil-testing.md) - Hardware-in-the-Loop testing
- [@context/skills/testing/pil-testing.md](../testing/pil-testing.md) - Processor-in-the-Loop testing
- [@context/skills/testing/test-automation.md](../testing/test-automation.md) - Test automation frameworks
- [@context/skills/safety/iso-26262-overview.md](../safety/iso-26262-overview.md) - ISO 26262 testing requirements
- [@context/skills/autosar/classic-platform.md](../autosar/classic-platform.md) - AUTOSAR model-based development

## Tools Required

| Tool | Purpose | Vendor |
|------|---------|--------|
| MATLAB/Simulink | Model development and testing | MathWorks |
| Simulink Test | Test harness and automation | MathWorks |
| Simulink Coverage | Model coverage analysis | MathWorks |
| Simulink Coder | Code generation for SIL | MathWorks |
| Embedded Coder | Production code generation | MathWorks |
| Stateflow | State machine modeling | MathWorks |
| MATLAB Test Manager | Test execution and reporting | MathWorks |
| Jenkins/GitHub Actions | CI/CD automation | Open-source/GitHub |

## Regulatory Context

| Region | Regulation | MIL Testing Relevance |
|--------|------------|----------------------|
| EU/UNECE | UN ECE R157 (ALKS) | MIL validation of ADAS algorithms |
| EU | Type Approval (EU) 2022/1426 | Model-based development evidence |
| US | FMVSS | Early algorithm verification |
| China | GB/T standards | MIL methodology aligned with international standards |
