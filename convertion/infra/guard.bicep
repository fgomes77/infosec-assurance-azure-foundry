// Deployment-time assertion helper: main.bicep passes 'ok' or an error text;
// anything but 'ok' fails validation / what-if before any resource changes.
@allowed(['ok'])
param publicAccessCheck string
output check string = publicAccessCheck
