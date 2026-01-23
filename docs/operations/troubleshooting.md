# Troubleshooting

Common issues and their solutions.

## Common Issues

### Application Issues

#### Service Won't Start
- Check logs for errors
- Verify environment variables
- Check database connectivity
- Verify dependencies installed

#### Database Connection Errors
- Check database is running
- Verify connection settings in `.env`
- Check network connectivity
- Review database logs

#### Performance Issues
- Check database query performance
- Review application logs
- Check resource usage
- Review recent changes

### Frontend Issues

#### Build Failures
- Check Node.js version
- Clear node_modules and reinstall
- Check for TypeScript errors
- Review build logs

#### API Connection Issues
- Verify backend is running
- Check CORS settings
- Review network requests
- Check authentication

## Debugging

### Backend Debugging
- Use Django debug toolbar
- Check application logs
- Use database query logging
- Review error traces

### Frontend Debugging
- Use browser dev tools
- Check network tab
- Review console errors
- Use React DevTools

## Getting Help

1. **Check Logs** - Review application logs
2. **Search Documentation** - Check this guide
3. **Review Recent Changes** - Check git history
4. **Create HITL** - If issue is complex, create HITL item

## Related Documentation

- [Operations](README.md) - Operations overview
- [Monitoring](monitoring.md) - Monitoring setup
- [Runbooks](runbooks/README.md) - Operational procedures
