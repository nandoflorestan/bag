r"""Utility module for the poor souls who have to deal with MySQL.

How to set this up on your server::

    sudo apt-get install python-setuptools virtualenvwrapper
    # Create a directory for this project
    mkdir ~/mysql-dumps; cd ~/mysql-dumps
    # Create a virtualenv and install the bag library in it
    mkvirtualenv -p `which python3` dumper
    easy_install -UZ bag

Then edit a file called dump_db.py with more or less the following content.
The example assumes you are using WordPress; read it carefully::

    #!/usr/bin/env python3

    ""\"Backs up MySQL database once.""\"

    from datetime import datetime
    from bag.dump_mysql import DumpMySQL

    dumper = DumpMySQL.from_wordpress_config(
        config_path='/home/deployer/my_wordpress_site/wp-config.php',
    )
    destination_path = str(datetime.utcnow())[:19] + '.sql.gz'
    dumper.dump(destination_path)

    # It is also possible to send the backup to an S3 bucket,
    # but please remember to secure access to the bucket:
    result = dumper.copy_to_s3(
        destination_path, aws_id='REDACTED', aws_secret='REDACTED',
        aws_region='REDACTED', bucket_name='production-db-backups')

Give permission for the above script to be executed::

    chmod +x dump_db.py

Run the script once to test it::

    ./dump_db.py

If it is working, create a shell script, called `dump_db.sh`, for cron to call::

    cd /home/deployer/mysql-dumps
    # Run dump_db.py under the appropriate virtualenv:
    /home/deployer/.virtualenvs/dumper/bin/python dump_db.py

Give permission for the above shell script to be executed::

    chmod +x dump_db.sh

Then add a cronjob for it with the command `crontab -e`::

    # Minute Hour Day Month Weekday Command
    07       */8  *   *     *       /home/deployer/mysql-dumps/dump_db.sh > /tmp/crondump 2>&1
    # The above creates a database backup every 8 hours.
"""

from subprocess import check_call
from bag.log import setup_rotating_logger
from bag.pathlib_complement import Path


class DumpMySQL:
    """Dumps MySQL database to SQL file. Can send the file to an S3 bucket."""

    def __init__(self, database, user, password, host='localhost',
                 dump_command_path='/usr/bin/mysqldump',
                 log_directory='.'):
        """Constructor."""
        self.host = host
        self.database = database
        self.user = user
        self.password = password
        self.dump_command_path = dump_command_path
        self.log = setup_rotating_logger(
            'dump_mysql', size=50 * 1000 * 1000, directory=log_directory)

    def get_dump_cmd(self, destination_path, gzip='gzip'):
        """Return list/command to dump this environment's database to SQL."""
        alist = [
            self.dump_command_path,
            '--skip-extended-insert',
            '--protocol=tcp',
            '-h' + self.host,
            '-u' + self.user,
            '-p' + self.password,
            self.database,
        ]
        if gzip:
            alist.append('|')
            alist.append(gzip)
        alist.append('>')
        alist.append("'" + str(destination_path) + "'")
        return alist

    def dump(self, destination_path, gzip='gzip'):
        """Actually perform the database dump.

        When you create a gzipped dump, you can read it like this::

            zcat path/to/my-dump.sql.gz | less
        """
        self.log.debug('Starting MySQL dump.')
        alist = self.get_dump_cmd(destination_path, gzip)
        check_call(' '.join(alist), shell=True)
        self.log.info('File created: {}'.format(destination_path))

    @classmethod
    def from_wordpress_config(cls, config_path='./wp-config.php',
                              encoding='utf-8', **kw):
        """Read WordPress configuration file to get database credentials."""
        import re

        def wp_setting(name):
            return re.compile(r"define\('{}', '([^']+)'\)".format(name))

        with open(config_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return cls(
            host=wp_setting('DB_HOST').search(content).group(1),
            database=wp_setting('DB_NAME').search(content).group(1),
            user=wp_setting('DB_USER').search(content).group(1),
            password=wp_setting('DB_PASSWORD').search(content).group(1),
            **kw)

    def copy_to_s3(self, path, aws_id, aws_secret, aws_region,
                   bucket_name, namespace=''):
        """Send the file ``path`` to an S3 bucket."""
        self.log.debug('Sending to S3 bucket...')
        # http://botocore.readthedocs.org/en/latest/
        # from botocore.exceptions import ClientError  # easy_install -UZ boto3
        from boto3.session import Session  # easy_install -UZ boto3
        session = Session(
            aws_access_key_id=aws_id,
            aws_secret_access_key=aws_secret,
            region_name=aws_region)
        s3 = session.resource('s3')
        bucket = s3.Bucket(bucket_name)
        if namespace and not namespace.endswith('/'):
            namespace = namespace + '/'

        with open(path, 'br') as content:
            result = bucket.put_object(
                Key=namespace + Path(path).name, Body=content)
        self.log.info(result)
        return result
