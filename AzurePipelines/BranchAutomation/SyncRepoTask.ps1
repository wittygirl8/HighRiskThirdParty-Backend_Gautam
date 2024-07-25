param(
  [string] $userName,
  [string] $ori_token,
  [string] $ori_Repo_link,
  [string] $ori_Repo_name,
  [string] $ori_branch,
  
  [string] $tar_token,
  [string] $tar_Repo_link,
  [string] $tar_branch
)

# Set up branch name cleaning
$SourceBranch=$ori_branch
Write-Host "Received source branch as $SourceBranch"

$CleanedSourceBranch=$SourceBranch.Replace("refs/heads/","")
Write-Host "Cleaned source branch to $CleanedSourceBranch"

$TargetBranch=$tar_branch
Write-Host "Received target branch as $TargetBranch"

$CleanedTargetBranch=$TargetBranch.Replace("refs/heads/","")
Write-Host "Cleaned target branch to $CleanedTargetBranch"

# Set up creds
$ori_base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(("{0}:{1}" -f $userName,$ori_token)))
$tar_base64AuthInfo = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes(("{0}:{1}" -f $userName,$tar_token)))

# Set up Repo
Write-Host "Cloning Branch $CleanedSourceBranch from $ori_Repo_link"
git config --global credential.authority basic
git -c http.extraHeader="Authorization: Basic $ori_base64AuthInfo" clone --single-branch --branch $CleanedSourceBranch $ori_Repo_link
#git config -l  #for debug only
cd $ori_Repo_name

# Set up Repo
Write-Host "Pushing Branch $CleanedTargetBranch onto $tar_Repo_link"
git -c http.extraHeader="Authorization: Basic $tar_base64AuthInfo" push $tar_Repo_link ${ori_branch}:${CleanedTargetBranch} --force

Write-Host "Process completed"