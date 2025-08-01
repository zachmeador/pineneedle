# a journal of the user's thoughts

idea for this came from the fact that I never know what resume is up to date, but usually none of them are. 

writing them is boring. you should always cater a resume to a posting but it's labor intensive. 

and probably most people now have llms write some or all of their resume. 

etc.. that's the core problem

## things i hate about the current state of the app

- the template systems don't make intuitive sense.
    - need to rethink it. 
        - there are content templates, sets the order and contents of a resume render. could remain as a markdown file. 
        - there are pdf templates, which determine the styling and rendering. more complex. 
- tui is ass. visually not nice, too many emojis.
    - the flow should be focused on: open app, add posting, generate resume (if confirmed the user likes the resume, save to markdown and pdf)
        - user can apply custom design params
- code feels a bit messy / hard to understand

## things i like about the current state of the app

- data storage implementation
- agents.py

## required features

### dev

- easy to extend and maintain code. lean on a framework if it makes the code simpler. 
    - i think pydantic-ai is a good idea

### usage

- DONE: user can supply raw text dumps of a job posting. it's cleaned by the app and stored in a semi-structured way. 
    - job postings are just whatever the user pastes in. the llm receiving it can decipher the important bits.
- DONE: user can "render" a resume for a particular posting, or a general one

- user can specify a "tone" for a render if they want. say, one with more casual language, more technical, etc. 
    - reason for this is sometimes the user will have intuition about the posting that won't be evident in context clues to the llm
    - don't overthink tones. could literally just be a string that goes into the system context construction
- user can also specify a certain model. and in this case a model includes params like: model provider, model name, temperature
- user fills in a set of markdown files for things like education, job experience, internships, etc.
    - the user is expected to use something sane in terms of a format but the llm can handle that
- resumes generated for postings are archived 
    - archive everything: job posting data, generated resume, model settings, prompts used, etc. no reason not to hoard the data.
    - state/storage is well-designed and in human readable formats
- cli app, but nice
- the user needs to be able to iterate in the render process. there need to be interactive steps in the cli for this, but keep it simple.
    - iteration means: user sees the render and can accept it, or provide feedback to the llm on what needs changed
- markdown to pdf rendering. otherwise this isn't fully solving the "no resume to having a shareable resume" pipeline
- the app will be sync, and not have multiple instances. so, use json for maintaining state for the app. have it live with the user's library of markdowns
- needs to be easy to use a local llm if the user wants to
- the resume rendering needs to be based off of a user-modified template library. app contains one simple template for now. 

## mcp server (not client)

I still barely understand how mcp works so i dunno if this needs to run its own server, or if you provide this app to an mcp server or whatever. but i'm thinking generally that this app should enable a smart llm to use all of its functionality. 

the tools:

read:

- read user's background
- read a job posting
    - read all job postings?

write:

- send a job posting to the parser
- generate a resume from a posting (with args obv)
- 

## boring stuff

- use python uv
- use dotenv and a .env for llm api keys