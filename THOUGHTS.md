# a journal of the user's thoughts

idea for this came from the fact that I never know what resume is up to date, but usually none of them are. 

writing them is boring. you should always cater a resume to a posting but it's labor intensive. 

and probably most people now have llms write some or all of their resume. 

etc.. that's the core problem

## required features

- easy to extend and maintain code. lean on a framework if it makes the code simpler. 
    - i think pydantic-ai is a good idea
- user can supply raw html dumps of a job posting. it's cleaned by the app and stored in a semi-structured way. 
    - job postings are just whatever the user pastes in. the llm receiving it can decipher the important bits.
- user can "render" a resume for a particular posting, or a general one
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

## boring stuff

- use python uv
- use dotenv and a .env for llm api keys