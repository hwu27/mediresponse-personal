from transformers import GPT2Tokenizer, GPT2LMHeadModel
from torch import cuda
from autocorrect import Speller
import re
import wordninja
import sys
sys.path.append('../utils') 
import utils 
import random

model = GPT2LMHeadModel.from_pretrained('./GPT2_MediResponse/SaveFile')
tokenizer = GPT2Tokenizer.from_pretrained('./GPT2_MediResponse/SaveFile')
device = 'cuda' if cuda.is_available() else 'cpu'
model = model.to(device)

def get_model_and_tokenizer():
    return model, tokenizer

# GENERATE TEXT
def generate_text(prompt, max_length=60):
    input_ids = tokenizer.encode(prompt, return_tensors='pt').to(device)

    chat_history_ids = model.generate(
        input_ids,
        max_length=max_length + len(input_ids[0]),  
        pad_token_id=tokenizer.eos_token_id,
        repetition_penalty= 1.005,
        do_sample = True,
        temperature=0.2,  
        top_p=0.88,        
        top_k=56,          
        no_repeat_ngram_size=2
    )

    response = tokenizer.decode(chat_history_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
    return response

# cleaning output
def clean_output(input_string):
    input_string = input_string.replace('"', "") # remove "
    input_string = input_string.replace('. . .', '...') # reformat ...
    
    input_string = re.sub(r'\s*([?,.!"])\s*', r'\1 ', input_string) # ensure space after punc

    input_string = input_string.strip() # leading and trailing whitespace

    input_string = re.sub(r'\s{2,}', ' ', input_string) # single space between words and after punctuation
    
    # punc before capitalized letter
    words = input_string.split()
    corrected_words = []
    for i, word in enumerate(words):
        if (word[0].isupper() and i != 0 and not words[i-1][-1] in '.!?'):
            # check to avoid adding a period if the previous word ends with certain punctuation
            if not words[i-1][-1] in ',:;':
                corrected_words[-1] += '.'
        corrected_words.append(word)
    input_string = ' '.join(corrected_words)
    
    # trim text to last punctuation
    m = re.search(r'([.!?])[^.!?]*$', input_string)
    if m:
        input_string = input_string[:m.start()+1]

    return input_string

# # prompt line 1 of 2
# emotion = ["anger", "fear", "sadness", "surprise"]
# chosen_emotion = random.choice(emotion) 
# prompt1 = "[BOS] [PERSONA] You are a relative of a hospitalized patient. The patient is in critical condition. You are feeling "
# prompt1 = prompt1 + chosen_emotion + ". "

# # prompt line 2 of 2
# setup = ["It is looking bad.", "We are doing our best."]
# chosen_setup = random.choice(setup)
# prompt2 = "[DOC] Your relative is in critical condition. "
# prompt2 = prompt2 + chosen_setup + "[PATIENT] "


# final response
def relative_response(input_string):
    response = generate_text(input_string) # initial output from model

    response = wordninja.split(response) # sometimes multiple words are joined together, we split
    response = ' '.join(response) # rejoin to make proper sentence

    response = clean_output(response) # further clean output, see function above

    # spelling of singluar words/autocorrect
    spell = Speller()
    response = spell(response)

    # now we split response into sentence, and classify if they are actually words of a relative
    sentences = re.split(r'(?<=[.!?])\s+', response)
    responded = False
    final_resp = ""

    for sentence in sentences:
        prediction = utils.classify('role', sentence)
        if prediction[0][1] == 1:
            responded = True
            final_resp += sentence + " "

        else:
            if responded == True:
                break

    final_resp = final_resp[:-1]

    return final_resp

# response = relative_response(prompt1 + prompt2)

# print("Setting: You encounter a relative of a hospitalized patient who has been recently informed about their critical condition. Upon hearing this news, they feel " + chosen_emotion + ".")
# print("Relative: " + response)

# for i in range(4):
#     doc_response = input("Doctor (You): ")
#     prompt2 = "[DOC] " + doc_response + " [PATIENT] "
#     response = relative_response(prompt1 + prompt2)
#     print("Relative: " + response)

