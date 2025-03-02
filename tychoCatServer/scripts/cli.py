import click
import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger=logging.getLogger("CAT SERVER")

#Alta o modificación de suministro
@click.command()
@click.argument('cmd',type=str)

def tychoCatServer(cmd):
    logging.info(f"COMMAND:{cmd}")
    if 'server' in cmd:
        logging.info(f"Starting server")
        from  ..tychoCatServer import runServer
        runServer()
    elif 'download' in cmd:
        logging.info(f"Starting download process")
        from  ..downloader import download
        download()
    elif 'update' in cmd:
        logging.info(f"Starting updater. ")
        from  ..updater import update        
        update()        
    elif 'info' in cmd:
        from ..config import printCfg
        printCfg()
    else:
        logging.error(f"COMMAND:{cmd} DOES NOT EXIST")
        