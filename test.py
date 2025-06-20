import argparse
import itertools
import logging
from typing import Annotated

from ollama import chat
from pydantic import BaseModel, StringConstraints, conset
from pypinyin import Style, pinyin


class Response(BaseModel):
    results: conset(Annotated[str, StringConstraints(max_length=10)], max_length=6)
    reason: Annotated[str, StringConstraints(max_length=500)]


def prune(hanzi, phrase, readings):
    if len(readings) <= 1:
        return readings

    prompt_1 = f'漢字「{hanzi}」是一個多音字，有以下讀音：{readings}。大多數情形下，多音字在一個短語中只有一個合適的讀音，但少數情形下可能會有多個讀音。請好好思考一下，在短語「{phrase}」中選擇被方括號括起來的漢字「{hanzi}」可能的拼音。寫下你的推理過程。'

    prompt_2 = f'使用 JSON 格式總結你的回答。請用 `results` 代表你選擇的「{hanzi}」的拼音，不要加註音調；用 `reason` 代表你這樣選擇的理由。'

    messages = []

    messages += [{'role': 'user', 'content': prompt_1}]

    response_1 = chat(
        messages=messages,
        model=model_name,
        options=dict(num_ctx=4096, num_predict=3584, seed=10)
    )

    logger.info(response_1.message.content)
    logger.info(
        f'prompt_eval_count={response_1.prompt_eval_count} eval_count={response_1.eval_count}'
    )

    messages += [
        {'role': 'assistant', 'content': response_1.message.content},
        {'role': 'user', 'content': prompt_2},
    ]

    response_2 = chat(
        format=Response.model_json_schema(),
        messages=messages,
        model=model_name,
        options=dict(num_ctx=4096, seed=10)
    )

    # Check for incomplete response from Ollama
    # Usually that means premature termination due to repeated tokens
    if not response_2.done:
        logger.info(response_2)
        return []

    validated_response = Response.model_validate_json(response_2.message.content)

    logger.info(validated_response)
    logger.info(
        f'prompt_eval_count={response_2.prompt_eval_count} eval_count={response_2.eval_count}'
    )

    return validated_response.results


def annotate_phrase(phrase, file_out):
    all_phrase_readings = pinyin(
        phrase, heteronym=True, style=Style.NORMAL, errors='exception'
    )
    pruned_phrase_readings = []

    for i, hanzi in enumerate(phrase):
        phrase_with_brackets = phrase[:i] + f'[{hanzi}]' + phrase[i+1:]
        pruned_readings = prune(
            hanzi, phrase_with_brackets, all_phrase_readings[i]
        )
        pruned_phrase_readings.append(pruned_readings)

    joined_phrase_readings = sorted(
        [' '.join(x) for x in itertools.product(*pruned_phrase_readings)]
    )
    for reading in joined_phrase_readings:
        logger.info(f'{phrase}\t{reading}')
        print(f'{phrase}\t{reading}', file=file_out)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--hanzi_tag', required=True, help='hanzi tag, e.g. \'樂\'')
    parser.add_argument('--model_name', required=True, help='model name, e.g. \'deepseek-r1:7b\'')
    args = parser.parse_args()

    return args


def main():
    # with open(f'luna_{hanzi_tag}.txt', 'r') as file_in, open(f'results_luna_{tag}.txt', 'a', buffering=1) as file_out:
    #    for line in file_in:
    #        phrase = line.strip()
    #        annotate_phrase(phrase, file_out=file_out)

    import sys
    phrase = '可口可樂公司'
    annotate_phrase(phrase, sys.stdout)


if '__main__' == __name__:
    args = parse_args()

    hanzi_tag = args.hanzi_tag
    model_name = args.model_name
    # hanzi_tag = '樂'
    # model_name = 'deepseek-r1:7b'
    model_tag = model_name.replace(':', '_').replace('.', 'p')
    tag = f'{hanzi_tag}_{model_tag}'

    logging.basicConfig(
        filename=f'results_luna_{tag}.log',
        filemode='a',
        format='%(asctime)s %(name)s:%(levelname)s:%(message)s',
        level=logging.INFO
    )
    logging.getLogger('httpx').propagate = False

    logger = logging.getLogger(__name__)

    main()
