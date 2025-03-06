# ISA Impact Dashboard Hosting Requirements

## Profiling Results

### Memory Usage
- **Dashboard Base Memory**: 162.47 MB
- **Simulation Memory**: 95.33 MB
- **Memory Increase During Simulation**: 1.94 MB

### CPU Usage
- **Dashboard Base CPU**: 0.80-0.90%
- **Simulation CPU**: Minimal (0.10%)

### Performance
- **Main Page Load Time**: 0.01 seconds
- **Navigation Request Time**: 0.01 seconds
- **Simulation Execution Time**: 0.22 seconds

## Recommended Hosting Specifications

Based on the profiling results, the following hosting specifications are recommended:

### Render Free Tier
- **Memory**: 512 MB (sufficient based on current usage)
- **CPU**: 0.1 vCPU (sufficient for basic usage)
- **Bandwidth**: 100 GB/month
- **Build Minutes**: 500/month

This tier should be adequate for:
- Small number of concurrent users (1-5)
- Infrequent simulations
- Basic dashboard usage

### Considerations for Upgrading

Consider upgrading to Render Starter tier ($7/month) if:
- You expect more than 5 concurrent users
- Users will be running multiple simulations in quick succession
- You need better response times for complex simulations

Render Starter tier provides:
- **Memory**: 2 GB
- **CPU**: 1 vCPU
- **Improved performance** for concurrent users

## Optimization Recommendations

To ensure optimal performance on the Free tier:

1. **Enable Caching**:
   - Implement Flask-Caching for expensive operations
   - Cache simulation results where possible

2. **Optimize Dashboard Code**:
   - Disable debug mode in production
   - Pre-compute static data where possible
   - Optimize callback functions

3. **Configure Gunicorn Properly**:
   - Set appropriate worker count (2-4)
   - Set appropriate timeout (120 seconds)
   - Enable thread workers

4. **Monitor Usage**:
   - Keep an eye on memory usage during peak times
   - Watch for performance degradation with multiple users

## Conclusion

The ISA Impact Dashboard should run adequately on Render's Free tier based on the current profiling results. The application uses approximately 162 MB of memory and minimal CPU resources in its base state, which is well within the Free tier's 512 MB limit.

If you anticipate higher usage or need better performance, consider implementing the optimization recommendations or upgrading to the Starter tier. 