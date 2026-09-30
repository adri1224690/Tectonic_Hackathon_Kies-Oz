# Tectonic_Hackathon_Kies-Oz
Solution to SDWorx Case by team Kies-Oz

The assumption used for the solution is based on that all information is already centralized (ie in a json document). The focus of this solution is to make the information returned by the search engine more relevant and trustworthy. To do this we try not only to focus on optimizing the system, but zooming out and focussing on the role of the client in finding a solution for the problem. The method is based on 3 things. 

1. The 'past success rate' of documents
  This means when a person uses a document to solve an issue, it gets more relevant (this sorts out trash documents). There are two ways to do this: 
    1. Documents get up/down votes 
    2. Documents get a number of how many uses it has had in the past (think references of an academic document). 
2. Building a client profile
  This client profile is used to give more relevant information based on these aspects: 
     1. Past questions
     2. Unique cases
     3. Company type (assumption 2: SDWorx already has a company profile with things like country, department...). This is used to relate to companies with similar problems. 
     4. Predictions of future problems.
       meaning predicting of the problems based on the problem profile and the company profile:
        1. if company has a profile and history then based on their history and problem history
        2. if company is a new client build its profile but no history, predict potential problems based on similar companies profiles
3. Problem profile
  1. Most recent precedent
  2. duration to solve
  3. cost of solving
  4. percentage of solving in the past. 
  5. most realiable ponits of conatc( emolyees that solved similar cases and whose cases are most referenced)
  6. prediction of potential new porblems based on this problem and past history of similar cases 
  
  
