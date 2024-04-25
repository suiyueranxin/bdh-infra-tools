# Code branches mapping

Here's a table describing the relationships of all code branches between *hanalite-releasepack* and *bdh-infra-tools* in different validations:

<escape>
  <table>
  <tr><th>Validation Type</th><th>hanaliate-releasepack project branch</th><th>bdh-infra-tools project branch</th><th>Relationship</th></tr>
  <tr>
    <td rowspan="2">Milestone Validation</td>
    <td>master milestone version with suffix '-ms', like '2.7.74-ms'</td>
    <td>latest code from master branch</td>
    <td rowspan="2">CI Framework will use the code from the same corresponding branch from bdh-infra-tools to verify the milestone build directly.</td>
  </tr>
  <tr>
    <td>stable milestone version without suffix '-ms', like '2.7.66'</td>
    <td>latest code from stable branch</td>
  </tr>
  <tr>
    <td rowspan="5">Hanalite-releasepack Push Validation</td>
    <td>master</td>
    <td>master</td>
    <td rowspan="5">bdh-infra-tools is configured as a gitmodule in hanalite-releasepack, which will be used as the code baseline of CI Framework test execution.</td>
  </tr>
  <tr>
    <td>stable</td>
    <td>stable</td>
  </tr>
  <tr>
    <td>rel-dhaas</td>
    <td>rel-dhaas</td>
  </tr>
  <tr>
    <td>rel-2.6</td>
    <td>rel-2.6</td>
  </tr>
  <tr>
    <td>other branches: rel-2.x</td>
    <td>Other branches: rel-2.x</td>
  </tr>
  <tr>
    <td rowspan="2">Hanalite-releasepack Dev Nightly Validation</td>
    <td>master</td>
    <td>master</td>
    <td rowspan="2">CI Framework will fetch the latest master/stable code from both hanalite-releasepack and bdh-infra-tools, and run the validation. </td>
  </tr>
  <tr>
    <td>stable</td>
    <td>stable</td>
  </tr>
</table>
</escape>

# Update git submodule commit id

In *hanalite-releasepack* Push Validation, if there's any update to *bdh-infra-tools* code branch, it won't take effect in validation immediately. Before the git submodule is updated, *hanalite-releasepack* still uses the original commit id on the corresponding code branch.

If you want to update the git submodule commit id, follow the commands below (take `master` branch for example):

```
git submodule update --init
git submodule update --remote -- bdh-infra-tools
git add bdh-infra-tools
git commit
git push origin @:refs/for/master
```