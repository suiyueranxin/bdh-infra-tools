from pandas import DataFrame as df
import os
import gzip
import pandas as pd
import numpy
import gc
import json
import sys
import send_job_report 


save_dir='/infrabox/upload/archive/log_combine'
temp_dir='/tmp'
#save_dir='/work/i547510/log/save'


def un_gz(file_name):

    # get the file_name
    f_name = file_name.split('/')[-2].replace(".gz", "")

    save_name = os.path.join(temp_dir , f_name)
    # extract
    g_file = gzip.GzipFile(file_name)
    #get the unzip file
    open(save_name, "wb+").write(g_file.read())
    g_file.close()



def extract():
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
    input_dir = '/infrabox/inputs/'
    #input_dir = '/work/i547510/log/input'
    input_list=[]
    #get all output folder
    dir_list = os.listdir(input_dir)
    dir_list.sort()
    for i in dir_list:
        if i.startswith('log_collection'):
            input_list.append(i)
    
    print(input_list)
    #extract to the save dir
    for i in input_list:
        file_list = os.listdir(input_dir + '/' + i)
        for j in file_list:
            if j.startswith('k8s_vora_log'):
                print(j)
                un_gz(input_dir + '/' + i + '/' + j)


def splitDf(dataframe,save_dir):
    print(dataframe.info(memory_usage='deep'))
    container_name_info=dataframe['container_name'].unique()
    if 'nan' in container_name_info:
        print("remove nan")
        container_name_info.remove("nan")
    for c_index,c_info in enumerate(container_name_info):
        temp_dataframe=dataframe[dataframe['container_name'].isin([c_info])]
        df=temp_dataframe.sort_values(by=['container_name','@timestamp'])
        c_name=str(c_info)
        save_file_name = os.path.join(save_dir,c_name)
        print("save_file_name is %s (%s)"%(save_file_name,c_index))
        exec("df.to_csv('%s.csv', index=False, header=True, mode='a+')"%(save_file_name))
        print(df.info(memory_usage='deep'))
        del df
        del temp_dataframe
        collected= gc.collect()
        print("collected items: %s"%collected)
        

def combine():
    if not os.path.exists(save_dir):
        os.makedirs(save_dir)  
    file_list = os.listdir(temp_dir)
    file_list.sort()
    #split all log_collect file
    for i in range(0,len(file_list)):
        df = pd.read_csv(temp_dir + '/'+ file_list[i],low_memory=False)
        splitDf(df,save_dir)
    del df
    tmp_list = os.listdir(save_dir)
    if 'nan.csv' in tmp_list:
        print("remove nan")
        tmp_list.remove("nan.csv")
    tmp_list.sort()
    print(tmp_list)
    for i in range(0,len(tmp_list)):
        df = pd.read_csv(save_dir + '/'+ tmp_list[i],low_memory=False)
        df = df.sort_values(by=['@timestamp'])
        df.to_csv(save_dir + '/'+ tmp_list[i], index=False, header=True, mode='w')
        del df
    print("combine done")

def upload():
    restAPIHost = os.environ.get('RESTAPI_HOST', 'https://api.dashboard.datahub.only.sap')
    restAPIPort = os.environ.get('RESTAPI_PORT', '30711')
    restAPIPath = os.environ.get('RESTAPI_PATH', '/api/v1/trd/logcombine')
    job = json.load(open('/infrabox/job.json', 'r'))
    voraVersion = os.environ['VORA_VERSION']
    voraMilestonePath = None
    componentVersions = None #json.loads(os.environ['ALL_COMPONENTS_VERSIONS'])
    subTitle = "combine"

    jsonObj = send_job_report.generateJsonObject(job, '/infrabox/inputs/build_copy_files/recent_commit_log.json', voraVersion, subTitle, voraMilestonePath, componentVersions)

    if jsonObj is not None:
        print ("Saving the request json to Archive")

    with open('/infrabox/upload/archive/request_json_data.json', 'w') as outfile:
            json.dump(jsonObj, outfile)

    send_job_report.sendReportToRestAPI(restAPIHost, restAPIPort, restAPIPath, jsonObj)

def main():
    extract()
    combine()
    upload()

if __name__ == '__main__':
    print ("Start to combine kubernetes log by container name...")
    main()