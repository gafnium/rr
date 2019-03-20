import pipes
import os
import sys
import logging
import subprocess

def rsync(src, dst, config):
    options = ('--delete', '--verbose', '--compress', '--archive', '-e', 'ssh -q')

    if config['filters'] :
        for filter in config['filters'].split('\n'):
            if filter != '':
              options += ('--filter', filter)

    command = ('rsync',) + options + (src + '/', dst + '/')

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


def send(local_dir, host, remote_dir, config):
    remote_path = '{}:{}'.format(host, remote_dir)
    return rsync(local_dir, remote_path, config)


def receive(local_dir, host, remote_dir, config):
    remote_path = '{}:{}'.format(host, remote_dir)
    return rsync(remote_path, local_dir, config)


def remote_exec(host, remote_dir, before_exec,  command):
    remote_env = ' '.join([
        '{}={}'.format(key[len('REMOTERUN_'):],pipes.quote(value)) for key, value in os.environ.items()
            if key.startswith('REMOTERUN_')])
    logging.info('remote environment: {}'.format(remote_env))
    full_command = 'export {remote_env} > /dev/null; cd {remote_dir}; {before_exec} {command}'.format(
        remote_env = remote_env,
        remote_dir = pipes.quote(remote_dir),
        before_exec = before_exec,
        command = ' '.join(map(pipes.quote, command)) if command else '$SHELL')
    local_command = 'ssh {args} -t {host} {command}'.format(
        args = '-q' if command else '',
        host = pipes.quote(host),
        command = pipes.quote(full_command))

    logging.info('Executing {}'.format(local_command))
    return os.system(local_command) == 0

