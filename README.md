# pinyin-annotation

To create a list of phrases containing the character "樂" from the [rime-luna-pinyin](https://github.com/rime/rime-luna-pinyin) dictionary (to use as input for test.py), you can follow these steps:
1. Clone the repository
```
git clone https://github.com/rime/rime-luna-pinyin.git
```
2. Search for the phrases
```
grep 樂 rime-luna-pinyin/luna_pinyin.dict.yaml | cut -f1 | sed '/^.$/d' | sort | uniq > luna_樂.txt
```
