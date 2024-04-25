#!/usr/bin/python

import base64
import datetime
from Crypto.Cipher import AES
from ansible.module_utils.basic import AnsibleModule


class instanceToken:
    def __init__(self, akey):
        self.iv = "InfraTeamMustWin"
        self.obj = AES.new(akey, AES.MODE_CFB, self.iv)

    def dateTodayStr(self):
        return datetime.datetime.today().strftime('%Y-%m-%d')

    def dateOffsetStr(self, daysNumber=10):
        return (datetime.datetime.today() + datetime.timedelta(daysNumber)).strftime('%Y-%m-%d')

    def encodeInfo(self, dictStr):
        return base64.urlsafe_b64encode(self.obj.encrypt(str(dictStr)))

    def decodeInfo(self, tokenStr):
        infoDict = {}
        dictStr = self.obj.decrypt(base64.urlsafe_b64decode(tokenStr))
        try:
            # pylint: disable=W0123
            contentDict = eval(dictStr)
            infoDict["info"] = contentDict
            infoDict["status"] = "success"
            infoDict["rawToken"] = tokenStr
        # pylint: disable=W0703
        except Exception as err:
            infoDict = {"status": "fail", "info": "exception found when decode token with error '" + str(err) + "'", "rawToken": tokenStr}
        return infoDict

    def encodeStr(self, rawStr):
        return base64.urlsafe_b64encode(self.obj.encrypt(str(rawStr)))

    def decodeStr(self, tokenStr):
        return self.obj.decrypt(base64.urlsafe_b64decode(str(tokenStr)))

def main():
    module = AnsibleModule(argument_spec=dict(
        request_user_email=dict(required=False, type='str'),
        request_type=dict(required=True, choices=['encode',
                                                  'decode',
                                                  'encode_str',
                                                  'decode_str'], type='str'),
        request_period=dict(required=False, type='int'),
        request_project=dict(required=False, type='str'),
        request_description=dict(required=False, type='str'),
        key_string=dict(required=True, type='str'),
        raw_string=dict(required=False, type='str'),
        token_string=dict(required=False, type='str'),))

    instance_token = instanceToken(module.params['key_string'])

    try:
        if module.params['request_type'] == 'encode':
            infoDict = {}
            infoDict["user_email"] = module.params['request_user_email']
            infoDict["project"] = module.params['request_project']
            infoDict["created_at"] = instance_token.dateTodayStr()
            infoDict["valid_until"] = instance_token.dateOffsetStr(module.params['request_period'])
            infoDict["description"] = module.params['request_description']
            response = instance_token.encodeInfo(infoDict)
        elif module.params['request_type'] == 'decode':
            response = instance_token.decodeInfo(module.params['token_string'])
        elif module.params['request_type'] == 'encode_str':
            response = instance_token.encodeStr(module.params['raw_string'])
        elif module.params['request_type'] == 'decode_str':
            response = instance_token.decodeStr(module.params['token_string'])
        else:
            module.fail_json(msg="Unsupported request type:" + module.params['request_type'])
    # pylint: disable=W0703
    except Exception as e:
        module.fail_json(msg="exception found when execute this module", debug_msg=str(e))

    result = {}
    result['changed'] = True
    result['response'] = response

    module.exit_json(**result)


if __name__ == '__main__':
    main()
