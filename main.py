import simulator
import logging


logger = logging.getLogger(__name__)

def main():
    logging.basicConfig(filename='simulator.log', level=logging.INFO)
    logger.info('Started')
    

if __name__ == "__main__":
    main()