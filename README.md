# ISA Impact Simulation Dashboard

A dashboard for simulating the impact of Income Share Agreements (ISAs) for educational programs like Malengo. This tool allows users to explore different scenarios and understand how various parameters affect outcomes for both students and program sustainability.

## Overview

This dashboard simulates the financial and social impact of Income Share Agreements (ISAs) for educational programs. It provides insights into:

- Financial metrics (IRR, NPV, cash flow)
- Student outcomes across different percentiles
- Impact metrics in both utility and dollar terms
- Degree distribution analysis
- Cash flow projections

## Features

- Interactive simulation with adjustable parameters
- Comparison between TVET and University programs
- Visualization of financial and impact metrics
- Detailed percentile analysis
- Degree distribution tables
- Cash flow projections

## Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd <repository-directory>
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Usage

Run the dashboard locally:

```
python simulation_dashboard.py
```

The dashboard will be available at http://127.0.0.1:8050/

## Deployment on Render

This repository is configured for deployment on Render. To deploy:

1. Create a new Web Service on Render
2. Connect your repository
3. Use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn -c gunicorn_config.py simulation_dashboard:server`

## Model Parameters

### Program Types
- **TVET**: Technical and Vocational Education and Training
- **University**: Higher education programs

### Degree Types
- **VOC**: Vocational training
- **NURSE**: Nursing programs
- **NA**: No advanced education
- **BA**: Bachelor's degree
- **MA**: Master's degree

### Financial Parameters
- **ISA Cap**: Maximum amount to be paid back (72000 for University, 49500 for TVET)
- **ISA Percentage**: Percentage of income to be paid (14% for University, 12% for TVET)
- **Cost per Student**: 29000 for University, 16500 for TVET

## Model Structure

The simulation is built on several key components:

1. **Student Model**: Simulates individual student outcomes based on degree type
2. **Investment Pool**: Manages the financial aspects of the ISA program
3. **Impact Calculation**: Measures utility and financial impact across different metrics
4. **Percentile Analysis**: Examines outcomes across different student performance levels

## License

[Specify your license here]

## Acknowledgments

This dashboard was developed to analyze the impact of educational ISA programs like Malengo, which facilitates educational migration to high-income countries for students in low-income countries. 