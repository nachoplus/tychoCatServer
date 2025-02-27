import click
import logging


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
    elif 'updater' in cmd:
        logging.info(f"Starting updater. It will be run indefinidely")
        from  ..updater import update        
        update()        
    elif 'bootstrap' in cmd:
        logging.info(f"Starting bootstrap")
        from  ..bootstrap import bootstrap        
        bootstrap()           
    else:
        logging.error(f"COMMAND:{cmd} DOES NOT EXIST")