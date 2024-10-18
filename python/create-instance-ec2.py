import boto3
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import os

client = WebClient(token='xoxp')

ec2_client = boto3.client('ec2', region_name='region')

instance_ids = []

# this user_data_script for testing purpose when you create instance at frist.
user_data_script = '''<powershell>
# Install IIS
Install-WindowsFeature -name Web-Server -IncludeManagementTools
# Add a simple HTML file
New-Item -Path "C:\\inetpub\\wwwroot\\index.html" -Type "file" -Value "<html><body><h1>Hello from EC2</h1></body></html>"
</powershell>
'''

class EC2Manager:
    def __init__(self, region_name='us-east-1'):
        self.ec2_client = boto3.client('ec2', region_name=region_name)
        self.snapshot_id = 'snap-id'
        self.ami_id = 'ami-id'

    def create_instances(self, final_list,channel_id, user_id):    
        for i in range(0, len(final_list)):
            i = final_list[i]
            instance_response = self.ec2_client.run_instances(
                ImageId=self.ami_id,
                InstanceType='t2.2xlarge',
                KeyName='efs',
                MinCount=1,
                MaxCount=1,
                BlockDeviceMappings=[
                    {
                        'DeviceName': '/dev/sda1',
                        'Ebs': {
                            'VolumeSize': 500,
                            'VolumeType': 'gp2',
                            'DeleteOnTermination': True,
                            'SnapshotId': self.snapshot_id
                        },
                    },
                ],
                NetworkInterfaces=[
                    {
                        'SubnetId': 'subnet-id',
                        'DeviceIndex': 0,
                        'AssociatePublicIpAddress': True,
                        'DeleteOnTermination': True,
                        'Groups': ['sg-id']
                    }
                ],
                TagSpecifications=[
                    {
                        'ResourceType': 'instance',
                        'Tags': [
                            {
                                'Key': 'Name',
                                'Value': f'{i}'
                            }
                        ]
                    }
                ],
                Placement={
                    'AvailabilityZone': 'us-east-1b',
                },
                UserData=rf'''<powershell>
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        #Slack function to send message
        function Send-SlackMessage {{
            param(
                [string]$ChannelId,
                [string]$Message,
                [string]$WebhookUrl
            )

            $payload = @{{
                "text"    = $Message
            }} | ConvertTo-Json

            try {{
                $response = Invoke-RestMethod -Uri $WebhookUrl -Method Post -Body $payload -ContentType 'application/json'
                if ($response.ok -eq $false) {{
                    Write-Error "Failed to send message: $($response.error)"
                }}
            }} catch {{
            Write-Error "Error sending message: $_"
            }}
        }}
        #Slack credentails
        $webhookUrl = "https://hooks.slack.com/services/......"
        $time = Get-Date -Format 'yyyyMMdd_HHmmss'
        Function Log-Message([String]$Message)
        {{
            $filePath = "C:\recovery\log\$time.log"
            $directory = Split-Path -Path $filePath
            if (-not (Test-Path -Path $directory)) {{
                New-Item -Path $directory -ItemType Directory -Force
            }}
            Add-Content -Path $filePath -Value "$(Get-Date) :- $Message"
        }}
        Log-Message "Beginning exeuction of the script:"
        $fullbkp = "full-backup-0.0"
        $diffbkp = "diff-backup-0.0"
        $fullbkp_path = "C:\recovery\fullbkp"
        $diffbkp_path = "C:\recovery\diffbkp"
        if (!(Test-Path $fullbkp_path)) {{
            New-Item -ItemType Directory -Path $fullbkp_path
        }}
        if (!(Test-Path $diffbkp_path)) {{
            New-Item -ItemType Directory -Path $diffbkp_path
        }}
        $x = @(aws s3 ls $fullbkp)
        $y = @(aws s3 ls $diffbkp)
        # Initialize variables to store the latest folder information
        $latestFolder = $null
        $latestDate = [datetime]::MinValue
        # Iterate through each folder name
        Write-Output $x
        foreach ($folder in $x) {{
            $dateString = $folder -replace "PRE ", "" -replace "/", "" | ForEach-Object {{ $_.Trim() }}
            if ($dateString -match '^\d{{8}}$') {{
                try {{
                    # Parse the date string as a date
                    $folderDate = [datetime]::ParseExact($dateString, 'yyyyMMdd', $null)
                    # Check if this folder is the latest one
                    if ($folderDate -gt $latestDate) {{
                        $latestDate = $folderDate
                        $latestFolder = $folder
                    }}
                }} catch {{
                    Write-Warning "Failed to parse date: $dateString"
                }}
            }} else {{
                Write-Warning "Invalid date format: $dateString"
            }}
        }}
        Write-Output $latestFolder
        # Output the last uploaded folder
        if ($latestFolder) {{
            $cleanedLatestFolder = $latestFolder -replace "PRE ", "" -replace "/", "" | ForEach-Object {{ $_.Trim() }}
            
            Send-SlackMessage -Message "on server {i} : - Full Backup Downloading Proccess is Start now. \n Backup Date is $cleanedLatestFolder." -WebhookUrl $webhookUrl
            
            aws s3 cp "s3://$fullbkp/$cleanedLatestFolder/{i}/" $fullbkp_path --recursive --quiet 2>&1
            
            Send-SlackMessage -Message "on server {i} : - Full Backup Downloading Proccess Completed." -WebhookUrl $webhookUrl
            
        }} else {{
            Write-Output "No valid folders found."
        }}
        Write-Output $y
        # Iterate through each folder name
        foreach ($folder in $y) {{
            # Extract the date string from the folder name and trim any leading or trailing whitespace
            $dateString = $folder -replace "PRE ", "" -replace "/", "" | ForEach-Object {{ $_.Trim() }}
            # Check if the date string matches the yyyymmdd pattern
            if ($dateString -match '^\d{{8}}$') {{
                try {{
                    # Parse the date string as a date
                    $folderDate = [datetime]::ParseExact($dateString, 'yyyyMMdd', $null)
                    # Check if this folder is the latest one
                    if ($folderDate -gt $latestDate) {{
                        $latestDate = $folderDate
                        $latestFolder = $folder
                    }}
                }} catch {{
                    Write-Warning "Failed to parse date: $dateString"
                }}
            }} else {{
                Write-Warning "Invalid date format: $dateString"
            }}
        }}
        Write-Output $latestFolder
        # Output the last uploaded folder
        if ($latestFolder) {{
            $cleanedLatestFolder = $latestFolder -replace "PRE ", "" -replace "/", "" | ForEach-Object {{ $_.Trim() }}
            
            Send-SlackMessage -Message "on server {i} : -  diffential Backup Downloading Proccess is Start now.." -WebhookUrl $webhookUrl
            
            aws s3 cp "s3://$diffbkp/$cleanedLatestFolder/{i}/" $diffbkp_path --recursive --quiet 2>&1
            
            Send-SlackMessage -Message "on server {i} : - diffential Backup Downloading Proccess Completed." -WebhookUrl $webhookUrl
        
        }} else {{
            Write-Output "No valid folders found."
        }}

        #Restoring DB
        Send-SlackMessage -Message "on server {i} : - Databse restoring proccess start." -WebhookUrl $webhookUrl
        $server = "localhost\@$!2017"
        $username = "sa"
        $password = ""
        $connectionString = "Server=$server;User Id=$username;Password=$password;Database=master;TrustServerCertificate=True"

        $fullbkp_path = "C:\Recovery\fullbkp"
        $destination = "C:\temp"

        $zipFiles = Get-ChildItem -Path $fullbkp_path -Filter *.zip | Where-Object {{ $_.Name -like '*write uniq file contet to get all files*' }}
        $startTime = Get-Date
        $client_id = 0
        try {{
            foreach ($zipFile in $zipFiles) {{

                if (Test-Path $destination) {{
                    Remove-Item -Path $destination -Recurse -Force
                }}

                $client_id = ($zipFile -split '_')[1]

                Expand-Archive -Path $($zipFile.FullName) -DestinationPath $destination

                $extractedFiles = Get-ChildItem -Path $destination -Recurse | ForEach-Object {{ Get-ChildItem -Path $_.FullName -Recurse -File }}
                Write-Output $client_id

                if ($extractedFiles[0] -match "@$!ff") {{
                $ff = @"
DECLARE @dbName NVARCHAR(128) = N'@$!ff600_${{client_id}}';
DECLARE @logicalNameData NVARCHAR(128);
DECLARE @logicalNameLog NVARCHAR(128);
DECLARE @sql NVARCHAR(MAX);

SET @logicalNameData = N'@$!ff600';
SET @logicalNameLog = N'@$!ff600_log';

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'@$!ff600_${{client_id}}')
BEGIN
     SET @sql = N'CREATE DATABASE ' + QUOTENAME(@dbName);
     EXEC sp_executesql @sql;
END

-- Switch to the existing database context to retrieve file names
SET @sql = N'USE ' + QUOTENAME(@dbName) + ';
SELECT @logicalNameData_OUT = name 
FROM sys.database_files 
WHERE type_desc = ''ROWS'';

SELECT @logicalNameLog_OUT = name 
FROM sys.database_files 
WHERE type_desc = ''LOG'';';

-- Execute and capture results in the correct context
EXEC sp_executesql @sql, 
N'@logicalNameData_OUT NVARCHAR(128) OUTPUT, @logicalNameLog_OUT NVARCHAR(128) OUTPUT',
@logicalNameData_OUT = @logicalNameData OUTPUT, 
@logicalNameLog_OUT = @logicalNameLog OUTPUT;

RESTORE DATABASE [@$!ff600_$client_id]
FROM DISK = '$($extractedFiles[0])'
WITH REPLACE,
MOVE @logicalNameData TO 'C:\Program Files\Microsoft SQL Server\MSSQL14.@$!2017\MSSQL\DATA\@$!ff600_${{client_id}}.mdf',
MOVE @logicalNameLog TO 'C:\Program Files\Microsoft SQL Server\MSSQL14.@$!2017\MSSQL\DATA\@$!ff600_${{client_id}}_log.ldf';
"@

            Invoke-SqlCmd -ConnectionString $connectionString -Query $ff -QueryTimeout 180
                }}

                if ($extractedFiles[1] -match "@$!pp") {{
                $pp = @"
DECLARE @dbName NVARCHAR(128) = N'@$!pp_${{client_id}}';
DECLARE @logicalNameData NVARCHAR(128);
DECLARE @logicalNameLog NVARCHAR(128);
DECLARE @sql NVARCHAR(MAX);

SET @logicalNameData = N'@$!pp';
SET @logicalNameLog = N'@$!pp_log';

IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = @dbName)
BEGIN
    SET @sql = N'CREATE DATABASE ' + QUOTENAME(@dbName);
    EXEC sp_executesql @sql;
END
    
-- Switch to the existing database context to retrieve file names
SET @sql = N'USE ' + QUOTENAME(@dbName) + ';
SELECT @logicalNameData_OUT = name 
FROM sys.database_files 
WHERE type_desc = ''ROWS'';

SELECT @logicalNameLog_OUT = name 
FROM sys.database_files 
WHERE type_desc = ''LOG'';';

-- Execute and capture results in the correct context
EXEC sp_executesql @sql, 
N'@logicalNameData_OUT NVARCHAR(128) OUTPUT, @logicalNameLog_OUT NVARCHAR(128) OUTPUT',
@logicalNameData_OUT = @logicalNameData OUTPUT, 
@logicalNameLog_OUT = @logicalNameLog OUTPUT;


-- Restore the database using the correct logical file names
RESTORE DATABASE [@$!pp_$client_id]
FROM DISK = '$($extractedFiles[1])'
WITH REPLACE,
MOVE @logicalNameData TO 'C:\Program Files\Microsoft SQL Server\MSSQL14.@$!2017\MSSQL\DATA\@$!pp_${{client_id}}.mdf',
MOVE @logicalNameLog TO 'C:\Program Files\Microsoft SQL Server\MSSQL14.@$!2017\MSSQL\DATA\@$!pp_${{client_id}}_log.ldf';
"@

            Invoke-SqlCmd -ConnectionString $connectionString -Query $pp -QueryTimeout 180
                }}
                Remove-Item -Path $destination -Recurse -Force
                Send-SlackMessage -Message "on server {i} : - $client_id has been successfully restored." -WebhookUrl $webhookUrl
            }}
        }} catch {{
            Send-SlackMessage -Message "on server {i} : - $client_id Error : $_" -WebhookUrl $webhookUrl
            Write-Output "Error : $_"
        }}
        $end_Time = Get-Date

        $executionTime = $end_Time - $startTime

        Write-Output $executionTime
        </powershell>
        <persist>true</persist>
        ''')

            instance_id = instance_response['Instances'][0]['InstanceId']
            instance_ids.append(instance_id)

        ec2_client.get_waiter('instance_running').wait(InstanceIds=instance_ids)

        describe_response = ec2_client.describe_instances(InstanceIds=instance_ids)
        for reservation in describe_response['Reservations']:
            for instance in reservation['Instances']:
                instance_id = instance['InstanceId']
                public_ip = instance.get('PublicIpAddress', 'N/A')
                instance_name = 'Unnamed'
                for tag in instance.get('Tags', []):
                    if tag['Key'] == 'Name':
                        instance_name = tag['Value']
                        break
                try:
                    # Send a message to a channel or user
                    response = client.chat_postMessage(
                        channel=channel_id,  # Replace with the channel or user ID
                        text=f"{instance_name} Public IP - {public_ip}"  # The message you want to send
                    )
                except SlackApiError as e:
                    pass
