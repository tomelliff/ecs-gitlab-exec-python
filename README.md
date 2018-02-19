# ECS Gitlab Executor hacking

Working out the flow of what needs to happen for there to be an ECS Gitlab executor. Easier for me to work this out in Python first and then implement it in Go.

### Brain dump of stuff to do:

- register runner does nothing with ecs
- when picking up a job it will create a task definition with the runner config plus the image+tag. Command should be 'sh' (not bash?)
	- what about services? these should be a multi container task with links?
	- on second run it should check that task definition is the same (image+tag/services not changed) and then just use it instead of creating again (does this really save any time over removing the task definition each time?)
		- if the task definition does need to change (eg image tag has changed) then it should be updated
		- what happens if the runner definition changes? only gets picked up when the job runs so if a mount point is added or different ecs cluster specified then we would need to change it too
		- maybe simpler to just throw the task definition away after every run
- it should then run the task with an override on the env vars, passing in variables from the job
- once the task is running it should then find the container instance it is running on and then get the ip address (use private if flag is set on runner, otherwise public) and connect to remote docker socket on container instance (runner must be able to reach the container instance on docker port and container instance must be exposing socket to 0.0.0.0/0
- from there just run the normal docker stuff, passing in commands as the docker executor does?
- when the job exits the task definition should remain unless the runner is being unregistered in which case it should remove all the task definitions it created

### TODO:

- how to get the container id or name from the task arn? need it to be able to exec into container
- create minimal ecs cluster allowing access to docker daemon remotely
    - `DOCKER_OPTS="-H tcp://0.0.0.0:2376"`
    - should look at what needs to be done for TLS communication as well (https://docs.docker.com/engine/security/https/#daemon-modes)
- run ECS tasks and then exec into them and stream the output back out
- handle services (linked containers in the task)
- test if it's worth keeping task definitions around if we potentially have to check them every single job run (image/services may have changed)
