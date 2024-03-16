# UNIVERSA - codebase for the hackathon

Agents in the Wild
Technical description:
Conceptualize the communication between agent and the world (i.e. Internet)
Implement base classes and methods for connecting with APIs and other external sources
Prepare a working example of an agent team utilizing the implemented solution
Create method(s) (following the base code) to enable choosing the proper connections for the agent team to use

Question 1: Can you give examples of the types of problems the agent teams might solve in the real world?

Designing & implementing software
Creating an architecture, choosing steps to implement it and actually doing it - this requires a lot of tools to work. Take a look at Devin AI - it utilizes a terminal, browsers the web and implements a safe evaluation environment for code execution.

Spreading content on social networks
In order to become a true Marketing Agent, we need not only skills in writing and curating content, but also in accessing different platforms and posting content there in their own specific manner. This requires the ability to access their channels and use them to perform its task.

Learning new things
When humans want to learn something new, rarely do they simply sit and think - most cases, we search for materials to broaden our knowledge and skills. Agents need to possess that ability to - whether they want to learn programming or become a scientist, they need to have the tools at their disposal to find, extract and absorb information.

General assisting
Whether it is sending emails, ordering food & groceries or controlling the smart house you live in, agents need to have an array of different tools to access platforms and devices in our lives.

Question 2: How easy should it be to connect the agent teams to external sources?

General solution
Most importantly the solution should be general - how do we create a module that allows for adding any number of tools in the future for agents to use? Of course, there will be some specific implementations of methods, but how can we give agents access to them, so that we do not have to make changes in them each time we want to create a completely new tool.

Think outside of the box
It is hard to foresee what type of tools the future brings. Let’s make this as easy as possible to connect new tools to agents - what if there is some unified protocol for creating tools? Perhaps some meta layer between the code of a specialized tool and an agent? Do not think about rigorous implementations, rather about generalized approaches that allow for using many different individual methods as one.
