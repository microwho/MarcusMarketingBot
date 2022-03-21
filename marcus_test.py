import openai
import speech_recognition as sr
import pyttsx3
from time import time,sleep


convo = list()
max_length = 20
with open('openaiapikey.txt', 'r') as infile:
    open_ai_api_key = infile.read()
openai.api_key = open_ai_api_key
greeting = "Hello, how can I help?"
farewell = "Okay. Talk later!"
purge_msg = "Confirmed. Purging all data."
speech_delay = 1.5


def listen_loop(mic):
    try:
        with mic as source:
            r.adjust_for_ambient_noise(source)
            audio = r.listen(source)
        return r.recognize_google(audio)
    except Exception as oops:
        #print('ERROR', oops)
        return None


def open_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as infile:
        return infile.read()


def save_memory(content, label):  # label is input or output
    filename = 'memories/%s_%s.txt' % (time(), label)
    with open(filename, 'w', encoding='utf-8') as outfile:
        outfile.write(content)


def gpt3_completion(prompt, engine='text-curie-001', temp=1.0, top_p=1.0, tokens=200, freq_pen=1.0, pres_pen=1.0, stop=['User:','MARCUS:']):
    max_retry = 5
    retry = 0
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
            filename = '%s_gpt3.txt' % time()
            with open('gpt3_logs/%s' % filename, 'w') as outfile:
                outfile.write('PROMPT:\n\n' + prompt + '\n\n==========\n\nRESPONSE:\n\n' + text)
            return text
        except Exception as oops:
            retry += 1
            if retry >= max_retry:
                return "GPT3 error: %s" % oops
            print('Error communicating with OpenAI:', oops)
            sleep(0.25)


def generate_response(convo, prompt_file):
    prompt = open_file(prompt_file)
    convo_text = ''
    for i in convo:
        convo_text += i + '\n'
    convo_text = convo_text.strip()
    prompt = prompt.replace('<<CONVO>>', convo_text)
    return gpt3_completion(prompt)


def end_convo(speech):
    if "goodbye" in speech:
        return True
    if "that's all" in speech:
        return True
    if "i'm done" in speech:
        return True
    if "thanks MARCUS" in speech:
        return True
    return False


def purge_data(speech):
    if "delete all data" in speech:
        return True
    if "delete data" in speech:
        return True
    if "purge all data" in speech:
        return True
    if "purge data" in speech:
        return True
    return False


def convo_loop(speech, tts, mic):
    global convo
    ticktock = 1
    tts.say(greeting)
    save_memory(greeting, 'output')
    sleep(speech_delay)
    tts.runAndWait()
    while True:
        # listen for dialog
        speech = listen_loop(mic)
        if not speech:
            continue  # loop again
        print('User:', speech)
        save_memory(speech, 'input')
        convo.append('User: %s' % speech)
        #  check if user has ended the conversation
        if end_convo(speech.lower()):
            tts.say(farewell)
            save_memory(farewell, 'output')
            sleep(speech_delay)
            tts.runAndWait()
            return
        #  check if user wants to purge data
        if purge_data(speech.lower()):
            
            tts.say(purge_msg)
            sleep(speech_delay)
            tts.runAndWait()
            save_memory(purge_msg, 'output')
            convo = list()
            continue
        #  if not, continue conversation
        if ticktock > 0:
            response = generate_response(convo, 'marcus_ask.txt')
        else:
            response = generate_response(convo, 'marcus_fact.txt')
        convo.append('MARCUS: %s' % response)
        print('MARCUS: ', response)
        save_memory(response, 'output')
        ticktock = ticktock * -1
        tts.say(response)
        sleep(speech_delay)
        tts.runAndWait()
        if len(convo) >= max_length:
            a = convo.pop(0)


if __name__ == '__main__':
    r = sr.Recognizer()
    tts = pyttsx3.init()
    voices = tts.getProperty('voices')
    #tts.setProperty('voice', voices[1].id)
    tts.setProperty('voice', voices[0].id)
    mic = sr.Microphone(device_index=2)
    while True:  # master loop
        speech = listen_loop(mic)
        if speech:
            if "hey marcus" in speech.lower() or "hello marcus" in speech.lower():
                convo_loop(speech, tts, mic)