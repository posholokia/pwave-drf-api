#!/bin/bash
DUMPFILE=${PGDATABASE}_$(date +%Y-%m-%d_%H:%M:%S).dump;
DB=$(docker ps --filter name=$PGCONTAINER -q)
echo $PGPASS | docker exec -i $DB bash -c "pg_dump -U $PGUSER -W -Fc -x $PGDATABASE -f /tmp/dumpfile.dump";
docker cp $DB:/tmp/dumpfile.dump ~/tmp/$DUMPFILE
docker exec -i $DB rm /tmp/dumpfile.dump;

printf "%s\n" "$AWSKEY" "$AWSSECRET" "$AWSREGION" "" | aws configure
aws s3 --endpoint-url=https://storage.yandexcloud.net cp ~/tmp/$DUMPFILE s3://$AWSBUCKET/postgresql/db_dumps/$DUMPFILE;

# Remove old backups
aws s3 ls --endpoint-url=https://storage.yandexcloud.net s3://$AWSBUCKET/postgresql/db_dumps --recursive |\
  awk '{print $NF}' | sort -r | sed -E "s|.*$PGDATABASE/(.*)\$|\1|g;/^\$/d" |\
  tail -n "+$(($BACKUPS_QUANTITY + 1))" |\
  xargs -I FILE aws s3 rm --endpoint-url=https://storage.yandexcloud.net s3://$AWSBUCKET/FILE;

rm ~/tmp/$DUMPFILE;
