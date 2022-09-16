from typing import Any
from mainHandyFunc import *
import validators
import cv2
import requests
from threading import Thread
from logging import config


class MainWorker:
    def __init__(self, runType=None) -> None:

        self._runtype = runType or 'threading'  # default runtype is 'threading'
        assert self._runtype in [
            'single', 'threading'], 'runtype must be single or threading'

        self._base_path = getWhereIsMain()
        self._input_path = os.path.join(self._base_path, '1_input')
        self._output_path = os.path.join(self._base_path, '2_output')
        self._json_data = self.getSettingJson()
        self._info_df = self.getRuntimeInfo()
        self._handlerArray = []

    def getSettingJson(self):
        # get main file name from setting json
        with open(os.path.join(self._base_path, '0_setting', 'setting.json'), encoding='utf-8') as json_file:
            data = json.load(json_file)

        return data

    def getRuntimeInfo(self, type=None) -> pd.DataFrame:
        data = self._json_data

        inputType = type or 'excelFile'

        logging.info(f'Main File -- {inputType} -- ' +
                     os.path.join(self._base_path, data['main_file']))

        data_dict = {
            'file_path': [],
            'file_name': [],
            'output_name': [],
            'time': [],
        }

        if inputType == 'excelFile':
            wb = openpyxl.load_workbook(os.path.join(
                self._base_path, data['main_file']))
            sheet_go = wb['GO']

            for idx in range(7, sheet_go.max_row):
                if sheet_go['E'+str(idx)].value is not None:
                    data_dict['file_path'].append(sheet_go['E'+str(idx)].value)
                    data_dict['file_name'].append(sheet_go['F'+str(idx)].value)

                    # check if the name is a dup name, then rename it with the row number to make it unique
                    if not sheet_go['G'+str(idx)].value in data_dict['output_name']:
                        data_dict['output_name'].append(
                            sheet_go['G'+str(idx)].value)
                    else:
                        out_name = str(idx)+'_' + \
                            str(sheet_go['G'+str(idx)].value)
                        data_dict['output_name'].append(out_name)

                    data_dict['time'].append(sheet_go['H'+str(idx)].value)
        else:
            logging.info(
                f'need to add new processing here for inputType == {inputType}')

        return pd.DataFrame.from_dict(data_dict).fillna('')

    def downloadVideo(self, url: str, ouput_file: str):
        """request to get the video, download it to local folder as ouput_file\nThis step should be use in multithread for time efficiency
        """

        output_file_name = ouput_file.split('\\')[-1].replace('.jpg', '.mp4')
        video_local_path = os.path.join(self._input_path, output_file_name)
        res = requests.get(url)
        with open(video_local_path, 'wb') as saveFile:
            saveFile.write(res.content)
        saveFile.close()
        return video_local_path

    def video2thumb_by_time(self, file_path, time, output_file):
        """be awared that file_path could also a url, not just a local file
        """
        if validators.url(file_path):
            logging.debug('trigger url download sequence')
            file_path = self.downloadVideo(file_path, output_file)
        else:
            logging.debug('default sequence')

        try:
            if os.path.exists(file_path):
                # read video
                vcap = cv2.VideoCapture(file_path)

                fps_int = round(vcap.get(cv2.CAP_PROP_FPS))  # get fps
                try:
                    total_length = round(
                        vcap.get(cv2.CAP_PROP_FRAME_COUNT) / vcap.get(cv2.CAP_PROP_FPS))
                except:
                    total_length = round(
                        vcap.get(cv2.CAP_PROP_FRAME_COUNT) / 30)
                logging.info(
                    'length: {} -- fps: {}'.format(total_length, fps_int))
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

    def run_as_mt(self):
        th_list = [ThreadWithReturnValue(the_handler=hd)
                   for hd in self._handlerArray]

        for th in th_list:
            logging.debug(
                f'LOALS>> RM_data_processing>> get_long_url {th.name}')
            th.start()

        for th in th_list:
            th.join()

        return [th._out_value for th in th_list]

    def main_ver_1_2(self):
        output_pd = self._info_df

        # adding cl
        output_pd['output_file_path'] = ''
        output_pd['output_file_name'] = ''

        # 1st loop
        for idx in range(0, len(output_pd)):
            file_path = output_pd['file_path'][idx]
            output_name = output_pd['output_name'][idx]

            if output_pd['file_name'][idx] != '':
                file_name = output_pd['file_name'][idx].split('.')[0]
            else:
                file_name = output_name
                # re-asign
                output_pd['file_name'][idx] = output_name

            logging.info('Processing -- {}'.format(file_name))

            # set default time = 1 if time in input df = ''
            if output_pd['time'][idx] != '':
                time = output_pd['time'][idx]
            else:
                time = 1

            output_file = os.path.join(
                self._output_path, '{}.jpg'.format(output_name))

            if self._runtype == 'threading':
                # multithread will adding target info to Handler
                # create handler
                self._handlerArray.append(Handler(self.video2thumb_by_time, {
                    'file_path': file_path, 'time': time, 'output_file': output_file}))
            else:
                # single thread will just simple run here
                if self.video2thumb_by_time(file_path, time, output_file):
                    output_pd['output_file_path'][idx] = output_file
                    output_pd['output_file_name'][idx] = '{}.jpg'.format(
                        output_name)

        # 2nd loop if multithread run
        if self._runtype == 'threading':
            self.run_as_mt()
            for idx in range(0, len(output_pd)):
                if self._handlerArray[idx]._out:
                    output_pd['output_file_path'][idx] = self._handlerArray[idx]._param['output_file']
                    output_pd['output_file_name'][idx] = '{}.jpg'.format(
                        output_pd['output_name'][idx])

        # write output excel file
        output_pd.to_excel(os.path.join(self._output_path,
                           'outputFile.xlsx'), index=False)

        # fomat output for human reading
        fommatExcelFile(os.path.join(self._output_path, 'outputFile.xlsx'))
        logging.info(
            'Write output file -- {}'.format(os.path.join(self._output_path, 'outputFile.xlsx')))


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


class Handler:
    """DON'T just simply call a function\n
    Use this Handler instead, it will cover: error handler, save input param, output param\n
    And can be used as input for  ThreadWithReturnValue\n
    call ._out to get the return of the function or the Exception if run fail
    """

    def __init__(self, func, param: dict) -> None:
        self._func = func
        self._param = param
        self._out: Any
        self._is_excute_start: bool = False
        self._is_excute_done: bool = False

    def excute(self):
        try:
            self._is_excute_start = True
            self._out = self._func(**self._param)
            self._is_excute_done = True
            return self._out
        except Exception as e:
            self.error_handler(e)

    def error_handler(self, e: Exception):
        print(f'handle error>> func: {self._func}\nerror: { str(e)}')
        self._out = e

    def __str__(self) -> str:
        return f'func: {self._func}, param:{self._param}'


class ThreadWithReturnValue(Thread):
    def __init__(self, the_handler: Handler):
        Thread.__init__(self)
        self._the_handler = the_handler
        self._out_value = None

    def run(self):
        logging.info(self.getName())
        self._out_value = self._the_handler.excute()


if __name__ == "__main__":

    # not display warnings
    warnings.simplefilter('ignore')

    if os.path.exists('logging.conf'):
        logging.config.fileConfig('logging.conf')  # type: ignore
    else:
        logging.basicConfig(format=r'#%(asctime)s:%(levelname)s\\ %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)  # , filename=os.path.join(base_path, '98_log', 'ezTW_runningLog-{}.txt'.format(startTime_str))

    logging.info('MAIN>> START!')
    bao = MainWorker(runType='single')

    bao.main_ver_1_2()
    logging.info('MAIN>> DONE!')
    os.system("pause")
