#!/bin/bash
DUMPFILE=$PGDATABASE_$(date +%Y-%m-%d_%H:%M:%S).dump;
docker exec -it $PGCONTAINER bash -c pg_dump -Fc -x $PGDATABASE > /tmp/$DUMPFILE;
printf "%s\n" "$AWSKEY" "$AWSSECRET" "$AWSREGION" "" | aws configure
aws s3 --endpoint-url=https://storage.yandexcloud.net cp /tmp/$DUMPFILE s3://$AWSBUCKET/postgresql/db_dumps/$DUMPFILE;
# Remove old backups
aws s3 ls  --endpoint-url=https://storage.yandexcloud.net s3://$AWSBUCKET/postgresql/db_dumps --recursive |\
  sort -r|sed -E "s|.*$PGDATABASE/(.*)\$|\1|g;/^\$/d"|\
  tail -n "+$((1))"|\
  xargs -I FILE aws s3 rm --endpoint-url=https://storage.yandexcloud.net s3://$AWSBUCKET/postgresql/db_dumps/FILE;
