#!/bin/sh
set -e

if [ "$APP_ENV" = "production" ]; then
  export NODE_ENV=production

  # Fallback for cases where build artifacts are missing.
  if [ ! -f "/app/.next/BUILD_ID" ]; then
    npm run build
  fi

  exec npm run start
else
  export NODE_ENV=development
  export WATCHPACK_POLLING=true
  export CHOKIDAR_USEPOLLING=true

  exec npm run dev
fi
