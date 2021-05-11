.DEFAULT_GOAL := package

.PHONY: package

clean:
	dotnet clean

init:
	dotnet tool update -g Amazon.Lambda.Tools

package: init
	cd OIMEngine && dotnet lambda package
