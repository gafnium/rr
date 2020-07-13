import pipes
import os
import logging
import subprocess
from filtertools import make_filters_args

def rsync(src, dst, config,  dry_run):
    options = ['--delete', '--verbose', '--compress', '--archive', '-e', 'ssh -q']

    if dry_run:
        options.append('--dry-run')
        
    command = ['rsync'] + options + make_filters_args(config) + [src + '/', dst + '/']

    logging.info('Remote syncing from {} to {} '.format(src, dst))
    logging.debug('Command: {}'.format(command))

    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    for line in process.stdout:
        logging.debug('rsync: ' + line.decode('utf-8').rstrip())
    for line in process.stderr:
        logging.error('rsync: ' + line.decode('utf-8').rstrip())
    result = (process.wait() == 0)

    if result:
        logging.info('Syncing done')
    else:
        logging.error('Syncing failed')
    return result


def send(local_dir, host, remote_dir, config,  dry_run):
    remote_path = '{}:{}'.format(host, remote_dir)
    return rsync(local_dir, remote_path, config,  dry_run)


def receive(local_dir, host, remote_dir, config,  dry_run):
    remote_path = '{}:{}'.format(host, remote_dir)
    return rsync(remote_path, local_dir, config,  dry_run)


def remote_exec(host, remote_dir, before_exec,  command,  dry_run):
    remote_env = ' '.join([
        '{}={}'.format(key[len('REMOTERUN_'):],pipes.quote(value)) for key, value in os.environ.items()
            if key.startswith('REMOTERUN_')])
    logging.info('remote environment: {}'.format(remote_env))
    full_command = 'export {remote_env} > /dev/null; cd {remote_dir}; {before_exec} {command}'.format(
        remote_env = remote_env,
        remote_dir = pipes.quote(remote_dir),
        before_exec = before_exec,
        command = ' '.join(command) if command else '$SHELL')
    local_command = 'ssh {args} -t {host} {command}'.format(
        args = '-q' if command else '',
        host = pipes.quote(host),
        command = pipes.quote(full_command))

    logging.info('Executing {}'.format(local_command))
    if dry_run:
        return 0;
        
    return os.system(local_command) == 0


        
    
    
    
    
