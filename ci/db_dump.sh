#!/bin/bash
DUMPFILE=$PGDATABASE_$(date +%Y-%m-%d_%H:%M:%S).dump;
echo "--$PGDATABASE--"
echo $PGPASS | docker exec -i $PGCONTAINER bash -c "pg_dump -U $PGUSER -W -Fc -x $PGDATABASE -f /tmp/dumpfile.dump";
docker cp $PGCONTAINER:/tmp/dumpfile.dump ~/tmp/$DUMPFILE
docker exec -i $PGCONTAINER rm /tmp/dumpfile.dump;

printf "%s\n" "$AWSKEY" "$AWSSECRET" "$AWSREGION" "" | aws configure
aws s3 --endpoint-url=https://storage.yandexcloud.net cp ~/tmp/$DUMPFILE s3://$AWSBUCKET/postgresql/db_dumps/$DUMPFILE;
# Remove old backups
aws s3 ls  --endpoint-url=https://storage.yandexcloud.net s3://$AWSBUCKET/postgresql/db_dumps --recursive |\
  sort -r|sed -E "s|.*$PGDATABASE/(.*)\$|\1|g;/^\$/d"|\
  tail -n "+$(($BACKUPS_QUANTITY + 1))"|\
  xargs -I FILE aws s3 rm --endpoint-url=https://storage.yandexcloud.net s3://$AWSBUCKET/postgresql/db_dumps/FILE;

rm ~/tmp/$DUMPFILE;
