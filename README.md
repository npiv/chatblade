# Chatblade
## A CLI Swiss Army Knife for ChatGPT

Chatblade is a versatile command-line interface (CLI) tool designed to interact with OpenAI's ChatGPT. It accepts piped input, arguments, or both, and allows you to save common prompt preambles for quick usage. Additionally, Chatblade provides utility methods to extract JSON or Markdown from ChatGPT responses.

**Note**: You'll need to set up your OpenAI API key to use Chatblade.

You can do that by either passing `--openai-api-key KEY` or by setting an env variable `OPENAI_API_KEY` (recommended). The examples below all assume an env variable is set.

## Install

### Latest and greatest

To stay up to date with the current main branch you can:
- check out the project, and run `pip install .`
- or `pip install 'chatblade @ git+https://github.com/npiv/chatblade'`

### Via pypi

The last released version can be installed with `pip install chatblade --upgrade`

### via Brew tap (slow...)

Offical Homebrew acceptance is pending, in the meantime you can use this brew tap: 
```
brew tap npiv/chatblade
brew install chatblade
```

## Documentation

### Making queries

#### A new conversation

You can begin any query by just typing. eg

```bash
chatblade how can I extract a still frame from a video at 22:01 with ffmpeg
```
<img width="650" alt="image" src="https://user-images.githubusercontent.com/452020/226869260-1dcd4faf-521c-466b-998a-fd5cfdc5b3c7.png">



#### viewing the last conversation

if you would like to view the last conversation just call it back with `-l`

```bash
chatblade -l
```

#### Continue the last conversation

To continue the conversation and ask for a change within the context, you can again use `-l` but with a query.

```bash
chatblade -l can we make a gif instead from 00:22:01 to 00:22:04
```

#### Picking between gpt-3.5 and 4

By default gpt-3.5 is used, you can switch at any point to 4 by using `-c 4`

#### Chatting interactively

If you would prefer to chat interactively instead just use `chatblade -i`.

#### Show streaming text (experimental)

You can also stream the responses, just like in the webui. At the end of the stream it will format the result. This can be combined in an interactive session 

```chatblade -s -i```

https://user-images.githubusercontent.com/452020/226891636-54d12df2-528f-4365-a4f3-e51cb025773c.mov


### Formatting the results

Responses that come back are always shown as markdown. Sometimes this may not be what you want, as it removes new lines, or because you are only interested in extracting a part of the result to pipe to another command.

In that case you have 2 options:
- `-r` for raw, which just prints the text as ChatGPT returned it, and doesn't pass it through markdown.
- `-e` for extract, which will try to detect what was returned (either a code block or json) and extract only that part.

Both options can be used either with a new query, e.g. 

```bash
chatblade -e write me a python boilerplate script that starts a server and prints hello world > main.py
```

or with the last result (json in this example)
```bash
chatblade -l -e | jq
```

### Piping content into chatblade

If we have long prompts we don't want to type everytime, or just want to provide context for our query we can pipe into chatblade.

e.g.

```bash
curl https://news.ycombinator.com/rss | chatblade given the above rss can you show me the top 3 articles about AI and their links -c 4
```

The piped input is placed above the query and sent to ChatGPT. 

<img src="assets/example3.png">

or 

```bash
chatblade what does this script do < script.sh
```

What gets sent to ChatGPT over the wire is:

```
piped input
-------
query
```

### Checking token count and estimated costs

If you want to check the approximate cost and token usage of a previous query, you can use the `-t` flag for "tokens."

We could do this when passing in a lot of context like in the example above for instance.

```bash
curl https://news.ycombinator.com/rss | chatblade given the above rss can you show me the top 3 articles about AI and their links -t
```

<img width="650" alt="image" src="https://user-images.githubusercontent.com/452020/226874588-28c53f53-1d19-4ce3-b7ec-b01c2f7cf75a.png">

This won't perform any action over the wire, and just calculates the tokens locally.

### Make custom prompts

We can also save common prompt configs for easy reuse. Any yaml file we place under ~/.config/chatblade/ will be picked up by the command.

So for example, given the following yaml called `etymology.yaml`, which contains:
```yaml
system: |-
  I want you to act as a professional Etymologist and Quiz Generator. You have a deep knowledge of etymology and will be provided with a word. 
  The goal is to create cards that quiz on both the etymology and finding the word by its definition.

  The following is what a perfect answer would look like for the word "disparage":

  [{
    "question": "A verb used to indicate the act of speaking about someone or something in a negative or belittling way.<br/> <i>E.g He would often _______ his coworkers behind their backs.</i>",
    "answer": "disparage"
  },
  {
    "question": "What is the etymological root of the word disparage?",
    "answer": "From the Old French word <i>'desparagier'</i>, meaning 'marry someone of unequal rank', which comes from <i>'des-'</i> (dis-) and <i>'parage'</i> (equal rank)"
  }]

  You will return answers in JSON only. Answer truthfully and if you don't know then say so. Keep questions as close as possible to the
  provided examples. Make sure to include an example in the definition question. Use HTML within the strings to nicely format your answers.

  If multiple words are provided, create questions and answers for each of them in one list. 
  
  Only answer in JSON, don't provide any more text. Valid JSON uses "" quotes to wrap its items.
```

We can now run a command and refer to this prompt with `-p etymology`:

```bash
chatblade -p etymology gregarious
```

<img src="assets/example5.png">

And since we asked for JSON, we can pipe our result to something else, e.g.:

```bash
chatblade -l -e > toanki
```

### Help

```
usage: Chatblade [-h] [-l] [-p PROMPT] [--openai-api-key KEY] [--temperature T] [-c {3.5,4}] [-i] [-s] [-e] [-r] [-t] [query ...]

a CLI Swiss Army Knife for ChatGPT

positional arguments:
  query                 Query to send to chat GPT

options:
  -h, --help            show this help message and exit
  -l, --last            display the last result. If a query is given the conversation is continued
  -p PROMPT, --prompt-config PROMPT
                        prompt config name, or file containing a prompt config
  --openai-api-key KEY  the OpenAI API key can also be set as env variable OPENAI_API_KEY
  --temperature T       temperature (openai setting)
  -c {3.5,4}, --chat-gpt {3.5,4}
                        chat GPT model
  -i, --interactive     start an interactive chat session. This will implicitly continue the conversation
  -s, --stream          Stream the incoming text to the terminal
  -e, --extract         extract content from response if possible (either json or code block)
  -r, --raw             print the last response as pure text, don't pretty print or format
  -t, --tokens          display what *would* be sent, how many tokens, and estimated costs
```
