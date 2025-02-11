from django.conf import settings

import logging
import os

def getLogger(name):
    logger = logging.getLogger(name)

    if not logger.handlers:
        formatter = logging.Formatter("%(asctime)s - %(message)s")

        save_to_file = True
        try:
            file_handler = logging.FileHandler(
                os.path.join(
                    settings.BASE_DIR,
                    'logs/{0}.log'.format(
                        name.lower().replace(' ', '_')
                    )
                )
            )
        except:
            save_to_file = False
        
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.setLevel(logging.DEBUG)
        if save_to_file:
            logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger