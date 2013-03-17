#! /bin/sh

echo "Python release:"
echo "1) Make sure you have updated the version number and translations."
echo "2) Make sure you have commited and pushed."
echo "3) Type the new version number. Example: 0.1.2. Or cancel with CTRL-C."
echo "Then I will test, register, sdist, upload, git tag and push tags."
read VERSION
./setup.py test  &&  ./setup.py register sdist upload  &&  git tag -a v$VERSION -m "Version $VERSION"  &&  git push --tags  &&  echo 'Now remember to increment the version number, add a "dev" suffix and commit.'
