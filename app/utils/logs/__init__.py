import os
import sys
from logging.config import dictConfig
from logging import Formatter
from flask import request

class RequestFormatter(Formatter):
    """Custom formatter that adds HTTP request details"""
    def format(self, record):
        record.url = request.url if request else 'no-request'
        record.method = request.method if request else 'no-method'
        record.remote_addr = request.remote_addr if request else 'no-ip'
        return super().format(record)

os.makedirs('logs', exist_ok=True)

dictConfig({
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'default': {
            'format': '[%(asctime)s][%(levelname)s][%(module)s][%(message)s]',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'error': {
            'format': '[%(asctime)s][%(levelname)s][%(module)s][%(lineno)d][%(message)s]',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'request_format': {
                '()': RequestFormatter,
                'format': '[%(asctime)s][%(levelname)s][%(module)s][%(method)s][%(url)s][%(remote_addr)s][%(message)s]',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
            'formatter': 'default',
            'level': 'INFO'
        },
        'file_debug': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/debug.log',
            'maxBytes': 1024*1024,
            'formatter': 'default',
            'backupCount': 3,
            'level': 'DEBUG'
        },
        'file_error': {
            'class': 'logging.FileHandler',
            'filename': 'logs/error.log',
            'formatter': 'error',
            'level': 'ERROR'
        },
        'views_handler': {
                'class': 'logging.handlers.RotatingFileHandler',
                'filename': 'logs/views.log',
                'maxBytes': 1024*1024,
                'backupCount': 3,
                'formatter': 'request_format',
                'level': 'DEBUG'
        }
    },
    'root': {
        'handlers': ['stdout', 'file_debug', 'file_error'],
        'level': 'DEBUG',
        'propagate': True
    },
    'loggers': {
        'views': {
            'handlers': ['stdout', 'views_handler'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
})
