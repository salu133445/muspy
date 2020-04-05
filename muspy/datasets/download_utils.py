import os, re
import logging
from tqdm import tqdm
import requests


def download_from_url(url, path=None, root='.data', overwrite=False):
    """
    Code modified from https://github.com/pytorch/text/blob/master/torchtext/utils.py
    Download file for Google Drive.
    Returns the path to the downloaded file.
    Arguments:
        url: the url of the file
        path: explicitly set the filename, otherwise attempts to
            detect the file name from URL header. (None)
        root: download folder used to store the file in (.data)
        overwrite: overwrite existing files (False)
    Examples:
        >>> url = 'http://www.quest.dcs.shef.ac.uk/wmt16_files_mmt/validation.tar.gz'
        >>> torchtext.utils.download_from_url(url)
        >>> '.data/validation.tar.gz'
    """

    def _process_response(r, root, filename):
        chunk_size = 16 * 1024
        total_size = int(r.headers.get('Content-length', 0))
        if filename is None:
            d = r.headers['content-disposition']
            filename = re.findall("filename=\"(.+)\"", d)
            if filename is None:
                raise RuntimeError("Filename could not be autodetected")
            filename = filename[0]
        path = os.path.join(root, filename)
        if os.path.exists(path):
            logging.info('File %s already exists.', path)
            if not overwrite:
                return path
            logging.info('Overwriting file %s.', path)
        logging.info('Downloading file {} to {}.'.format(filename, path))
        with open(path, "wb") as file:
            with tqdm(total=total_size, unit='B',
                      unit_scale=1, desc=path.split('/')[-1]) as t:
                for chunk in r.iter_content(chunk_size):
                    if chunk:
                        file.write(chunk)
                        t.update(len(chunk))
        logging.info('File {} downloaded.'.format(path))
        return path

    if path is None:
        _, filename = os.path.split(url)
    else:
        root, filename = os.path.split(path)

    if not os.path.exists(root):
        raise RuntimeError(
            "Download directory {} does not exist. "
            "Did you create it?".format(root))

    if 'drive.google.com' not in url:
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, stream=True)
        return _process_response(response, root, filename)
    else:
        # google drive links get filename from google drive
        filename = None

    logging.info('Downloading from Google Drive; may take a few minutes')
    confirm_token = None
    session = requests.Session()
    response = session.get(url, stream=True)
    for k, v in response.cookies.items():
        if k.startswith("download_warning"):
            confirm_token = v

    if confirm_token:
        url = url + "&confirm=" + confirm_token
        response = session.get(url, stream=True)

    return _process_response(response, root, filename)


if __name__ == "__main__":
    # Lakh Midi
    download_from_url('http://hog.ee.columbia.edu/craffel/lmd/lmd_full.tar.gz')
    # NMD
    # download_from_url('http://abc.sourceforge.net/NMD/nmd/NMD.zip')
    # MAESTRO
    # download_from_url('https://storage.googleapis.com/magentadata/datasets/maestro/v2.0.0/maestro-v2.0.0.zip')
    #
    # JSB
    # download_from_url('http://www-etud.iro.umontreal.ca/~boulanni/JSB%20Chorales.zip')
    # PIANO MIDI
    # download_from_url('http://www-etud.iro.umontreal.ca/~boulanni/Piano-midi.de.zip')

    # TODO: BPS_FH, (https://github.com/Tsung-Ping/functional-harmony), git clone?
    # TODO: Musedata, where is the data?
