# goatgoat

A full stack application to track who "[got your goat](https://www.phrases.org.uk/meanings/get-your-goat.html)", when, and why. 

## Under-the-hood

This is a Flask app that is running GraphQL via [Graphene](https://docs.graphene-python.org/projects/sqlalchemy/en/latest/tutorial/) and SQLAlchemy. It uses celery workers for some asynchronus tasks. There is no front-end framework, it's all plain JavaScript inlined in the templates. 

## License

(Modified MIT license)

Copyright © 2022 TWright

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated 
documentation files (the “Software”), to deal in the Software without restriction, including without 
limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies 
of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

- The software is not allowed to be used for NFT's or any blockchain related project. Yes, even ones that are based on proof-of-work.
- The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
