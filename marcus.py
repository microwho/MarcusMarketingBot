import re
import os
import json
import openai
from time import time,sleep
import tensorflow_hub as hub
import numpy as np


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def save_file(filepath, content):
    with open(filepath, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


def save_log(payload):
    filename = 'chat/log_%s.json' % time()
    with open(filename, 'w', encoding='utf-8') as outfile:
        json.dump(payload, outfile, ensure_ascii=False, sort_keys=True, indent=1)


def load_logs():
    files = os.listdir('chat/')
    result = list()
    for file in files:
        content = open_file('chat/' + file)
        result.append(json.loads(content))
    return result


openai.api_key = open_file('openaiapikey.txt')


def gpt3_completion(prompt, engine='text-davinci-002', temp=1.1, top_p=1.0, tokens=100, freq_pen=0.0, pres_pen=0.0, stop=['USER:']):
    max_retry = 5
    retry = 0
    prompt = prompt.encode(encoding='ASCII',errors='ignore').decode()
    while True:
        try:
            response = openai.Completion.create(
                engine=engine,
                prompt=prompt,
                temperature=temp,
                max_tokens=tokens,
                top_p=top_p,
                frequency_penalty=freq_pen,
                presence_penalty=pres_pen,
                stop=stop)
            text = response['choices'][0]['text'].strip()
            text = re.sub('\s+', ' ', text)
            filename = '%s_gpt3.txt' % time()
            save_file('gpt3_logs/%s' % filename, prompt + '\n\n==========\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return 'GPT3 error: %s' % oops
            print('Error communicating with OpenAI:', oops)
            print(prompt)
            exit()
            sleep(1)


def similar_logs(vector):
    results = list()
    chat = load_logs()
    for i in chat:
        score = np.dot(i['vector'], vector)
        if score >= 1.0:
            continue
        info = i
        info['score'] = score
        results.append(info)
    ordered = sorted(results, key=lambda d: d['score'], reverse=True)
    try:  # just hack off the ordered list
        ordered = ordered[0:10]
        return ordered
    except:  # if it barfs, send back the whole list because it's too short
        return ordered



if __name__ == '__main__':
    embed = hub.load("https://tfhub.dev/google/universal-sentence-encoder-large/5")  # USEv5 is about 100x faster than 4
    conversation = ['USER: Hey Marcus','MARCUS: Hey there! How can I help? Also, did you know that creating content regularly helps with your SEO score?']
    print('==============\n\nMARCUS: Hey there! How can I help? Also, did you know that creating content regularly helps with your SEO score?')
    similar = list()
    while True:
        a = input('\nUSER: ')
        conversation.append('USER: %s' % a)
        block = '\n\n'.join([i['dialog'] for i in similar])
        block += '\n\n'.join(conversation) + '\n'
        prompt = open_file('prompt_marcus.txt').replace('<<CONVERSATION>>', block)
        response = gpt3_completion(prompt)
        print('\n', response)
        conversation.append(response)
        vectors = embed([a, response]).numpy().tolist()
        save_log({'dialog': 'USER: %s' % a, 'vector': vectors[0]})
        save_log({'dialog': response, 'vector': vectors[1]})
        similar = similar_logs(vectors[0])
        if len(conversation) > 20):
            b = conversation.pop(0)