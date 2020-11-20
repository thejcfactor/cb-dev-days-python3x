import datetime

def output_message(obj, msg=None):
    if msg:
        output = '{0}: {1}'.format(datetime.datetime.utcnow(), msg)
        print(output)

    print(obj)