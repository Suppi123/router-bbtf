import json
import logging


def write_result(output_file, result):
    """
    Write result to given file.
    :param output_file:
    :param result:
    :return:
    """
    result_list = list()
    try:
        with open(output_file) as fo:
            result_list = json.load(fo)
            fo.close()
    except OSError as e:
        logging.info(f'No file {output_file}. Create one.')

    result_list.append(result)
    with open(output_file, 'w') as f:
        json.dump(result_list, f)
        f.close()
