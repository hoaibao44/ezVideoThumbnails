from mainHandyFunc import *
import cv2


def video2thumb_by_time(file_path, time, output_file):
    try:
        if os.path.exists(file_path):
            # read video
            vcap = cv2.VideoCapture(file_path)

            fps_int = round(vcap.get(cv2.CAP_PROP_FPS))  # get fps
            try:
                total_length = round(
                    vcap.get(cv2.CAP_PROP_FRAME_COUNT) / vcap.get(cv2.CAP_PROP_FPS))
            except:
                total_length = round(vcap.get(cv2.CAP_PROP_FRAME_COUNT) / 30)
            logging.info('length: {} -- fps: {}'.format(total_length, fps_int))
            # print('video solution {}x{}'.format(
            #     vcap.get(cv2.CAP_PROP_FRAME_WIDTH), vcap.get(cv2.CAP_PROP_FRAME_HEIGHT)))

            # if time surpass total length then time = 1 (s)
            if time > total_length:
                time = total_length
                logging.warn(
                    'time > max_length of video: set time = {}'.format(str(total_length)))

            iFrame = 0
            while True:
                iFrame += 1
                ret, frame = vcap.read()

                if not ret:
                    logging.error('error')
                    vcap.release()

                    cv2.destroyAllWindows()
                    return False

                if iFrame == vcap.get(cv2.CAP_PROP_FRAME_COUNT) and ret:
                    logging.warn(
                        'reach last frame: set last frame as thumbnails')
                    # cv2.imwrite(output_file, frame)

                    imwrite(output_file, frame)
                    vcap.release()
                    cv2.destroyAllWindows()
                    return True

                if round(iFrame/fps_int, 2) >= time:
                    # cv2.imwrite(output_file, frame)
                    imwrite(output_file, frame)

                    # Release all space and windows once done
                    vcap.release()
                    cv2.destroyAllWindows()
                    return True

        else:
            logging.warn('File not exists -- {}'.format(file_path))
            return False
    except Exception as e:
        logging.error('ERROR at -- {}'.format(file_path))
        print(e)
        return False


def auto_generated():

    all_files = get_cr_folder(input_path)

    output_pd = pd.DataFrame()
    for cl in ['in_file_name', 'in_file_path', 'out_file_1s', 'out_file_2s', 'out_file_3s']:
        output_pd[cl] = ''

    for idx, my_file in enumerate(all_files):
        file_path = all_files[idx][1]

        output_pd.loc[idx] = [all_files[idx][0], all_files[idx][1], '', '', '']

        times = [1, 2, 3]
        for time in times:
            output_file = os.path.join(
                output_path, '{}-sec_{}.jpg'.format(all_files[idx][0], str(time)))

            if video2thumb_by_time(file_path, time, output_file):
                output_pd['out_file_{}s'.format(str(time))][idx] = output_file

    output_pd.to_excel('outputFile.xlsx', index=False)
    fommatExcelFile(os.path.join(base_path, 'outputFile.xlsx'))


def imwrite(filename, img, params=None):
    try:
        ext = os.path.splitext(filename)[1]
        result, n = cv2.imencode(ext, img, params)

        if result:
            with open(filename, mode='w+b') as f:
                n.tofile(f)
            return True
        else:
            return False
    except Exception as e:
        print(e)
        return False


if __name__ == "__main__":
    global base_path, input_path, output_path

    base_path = getWhereIsMain()

    input_path = os.path.join(base_path, '1_input')
    output_path = os.path.join(base_path, '2_output')
    # not display warnings
    warnings.simplefilter('ignore')
    logging.basicConfig(format=r'#%(asctime)s:%(levelname)s\\ %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S', level=logging.INFO)  # , filename=os.path.join(base_path, '98_log', 'ezTW_runningLog-{}.txt'.format(startTime_str))

    logging.info('Base_path: {base_path}'.format(
        base_path=base_path))

    output_pd = get_file_info()
    output_pd = output_pd.fillna('')

    logging.info('Get info OK')
    output_pd['output_file_path'] = ''
    output_pd['output_file_name'] = ''

    for idx in range(0, len(output_pd)):
        file_path = output_pd['file_path'][idx]
        file_name = output_pd['file_name'][idx].split('.')[0]
        output_name = output_pd['output_name'][idx]

        logging.info('Processing -- {}'.format(file_name))

        if output_pd['time'][idx] != '':
            time = output_pd['time'][idx]
        else:
            time = 2

        output_file = os.path.join(output_path, '{}.jpg'.format(output_name))

        if video2thumb_by_time(file_path, time, output_file):
            output_pd['output_file_path'][idx] = output_file
            output_pd['output_file_name'][idx] = '{}.jpg'.format(output_name)

    output_pd.to_excel(os.path.join(base_path, '2_output',
                       'outputFile.xlsx'), index=False)
    fommatExcelFile(os.path.join(base_path, '2_output', 'outputFile.xlsx'))
    logging.info('Write output file -- {}'.format(os.path.join(base_path,
                 '2_output', 'outputFile.xlsx')))
    os.system("pause")
