import os
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler
import subprocess
import json
from datetime import datetime
import socket
import re
import time
from dotenv import load_dotenv
from ec2_manager import EC2Manager
load_dotenv()

instance = EC2Manager()

app = App(token=os.getenv('user_token'))

front_as_back = [
    {
        "text": {
            "type": "plain_text",
            "text": "server_name",
            "emoji": True
        },
        "value": "server_ip"
    },
    {
        "text": {
            "type": "plain_text",
            "text": "server_name",
            "emoji": True
        },
        "value": "server_ip"
    },
    {
        "text": {
            "type": "plain_text",
            "text": "server_name",
            "emoji": True
        },
        "value": "server_ip"
    }
]
ip = { 
        "server_ip" : "server_name" ,
        "server_ip" : "server_name" ,
        "server_ip" : "server_name"
}

options_pattern = r"^(server1|server2|server3|server4)$"

@app.message(re.compile(options_pattern, re.IGNORECASE))
def message_hello(message, say, client):
    print(message)
    user = message['user']
    channel = message['channel']
    initial_message = client.chat_postMessage(
    channel=channel,
    text=f"Hello <@{user}>, checking the status of {message['text']}..."
    )

    output = subprocess.run(
    ["ping", "-c", "4", f"{message['text']}.complete_url.com"],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE
    )

    output_str = output.stdout.decode()
    # Determine the status message
    if "0% packet loss" in output_str or "bytes from" in output_str:
        status_message = f"Hello <@{user}>, {message['text']} is up :)"
    else:
        status_message = f"Hello <@{user}>, {message['text']} is down :("
    
    # Update the initial message with the result
    client.chat_update(
        channel=channel,
        ts=initial_message['ts'],
        text=status_message,
        blocks=[
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": status_message
                }
            }
        ]
    )


# Listens to incoming messages that contain "hello"
@app.command("/newday")
def handle_newday_command(ack, body, say):
    # Acknowledge the command
    ack()
    user_id = body.get('user_id', 'unknown_user')

    # say() sends a message to the channel where the event was triggered
    result = say(
        blocks=[
            {
                "type": "section",
                "block_id": "section678",
                "text": {
                    "type": "mrkdwn",
                    "text": f"Hey <@{user_id}> Please select server."
                },
                "accessory": {
                    "action_id": "select_option",
                    "type": "static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an option",
                        "emoji": True
                    },
                    "options": front_as_back
                },
            },
            {
                "type": "input",
                "block_id": "input_block",
                "label": {
                    "type": "plain_text",
                    "text": "Client ID"
                },
                "element": {
                    "type": "plain_text_input",
                    "action_id": "input_client_id"
                }
            },
            {
                "type": "actions",
                "block_id": "actionblock789",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Submit",
                            "emoji": True
                        },
                        "value": "submit_client_id",
                        "action_id": "submit_button"
                    }
                ]
            }
        ]
    )

    app.context['message_ts'] = result['ts']

@app.action("select_option")
def handle_option(ack):
    # Acknowledge the action
    ack()

@app.action("submit_button")
def handle_button(ack, body, client):
    # Acknowledge the action
    ack()
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    ts = body["message"]["ts"]

    # Extract client ID and selected option from the state
    state_values = body["state"]["values"]
    client_id = state_values["input_block"]["input_client_id"]["value"]
    print(state_values)
    selected_option = state_values["section678"]["select_option"]["selected_option"]["value"]
    
    inventory_content = "[servers]\n"
    inventory_content += f"{selected_option} sql_name={ip[selected_option]}\\\ASI2017\n"
    inventory_content += "\n[servers:vars]\n"
    inventory_content += "ansible_user=Administrator\n"
    inventory_content += "ansible_password=password"
    inventory_content += "ansible_connection=winrm\n"
    inventory_content += "ansible_winrm_server_cert_validation=ignore\n"
    inventory_content += "ansible_port=5986\n"
    with open("/home/user_name/Desktop/compute/new_day/inventory", "w") as inventory_file:
        inventory_file.write(inventory_content)
    sql_query = f"'SELECT maxDate AS MaxDate FROM @$!600_{client_id}.dbo.fMinMaxDate;'"
    command = f'ANSIBLE_STDOUT_CALLBACK=json ansible-playbook -i /home/user_name/Desktop/compute/new_day/inventory /home/user_name/Desktop/compute/new_day/new_day.yaml --extra-vars "sql_query={sql_query}"'
    result = sql_result(command)
    #Update the message to remove the input block and show a confirmation message
    if result == "Invalid Client ID or Server.":
        client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hello <@{user_id}>, Please check Server or client ID as it's seems Invalid."
                    }
                }
            ]
        )
        
    else:
        client.chat_update(
            channel=channel_id,
            ts=ts,
            blocks=[
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"Hello <@{user_id}>, \n*{str((datetime.strptime(result, '%Y-%m-%d %H:%M:%S.%f')).date())}* is NewDay of {client_id}."
                    }
                }
            ]
        )

def sql_result(command):
    #Get out put and send it to Frontend
    print(command)
    sql_result = subprocess.run(command, shell=True, capture_output=True, text=True)
    completed_process = sql_result
    stdout_data = completed_process.stdout
    result_data = json.loads(stdout_data)
    for play in result_data.get("plays", []):
        for task in play.get("tasks", []):
            hosts = task.get("hosts", {})
            for host, details in hosts.items():
                for i in ip:
                    if ip[i] == host:
                        host = i
                if details.get("changed") == False:
                    stdout_lines = details.get("msg", [])
                    result = stdout_lines
                    return(result)
                else:
                    stdout_lines = details.get("stdout_lines", [])
                    print(stdout_lines)
                    header_line = stdout_lines[0]
                    data_lines = stdout_lines[2:-1]
                    column_names = [column.strip() for column in header_line.split()]
                    rows = []
                    if len(column_names) > 1:
                        for data_line in data_lines:
                            values = [value.strip() for value in data_line.split()]
                            row = dict(zip(column_names, values))
                            rows.append(row)
                            data = {
                                'column_names': column_names,
                                'rows': rows
                            }
                        try:
                            result = data
                        except Exception as e:
                            result = "Invalid Client ID or Server."
                    else:
                        try:
                            result = stdout_lines[2]
                        except:
                            result = stdout_lines
                    return(result)

with open('temp_access.txt', 'w'):
    pass

def add_authorized_user(user_id):
    with open('authorized_users.txt', 'a') as file:
        file.write(user_id + '\n')

def add_temp_user(user_id):
    with open('temp_access.txt', 'a') as file:
        file.write(user_id + '\n')

def is_user_authorized(user_id):
    with open('authorized_users.txt', 'r') as file:
        authorized_users = file.read().splitlines()
        return user_id in authorized_users
    
def is_temp_user_authorized(user_id):
    with open('temp_access.txt', 'r') as file:
        authorized_users = file.read().splitlines()
        return user_id in authorized_users

@app.command("/sev1")
def sev1(ack, body, say, client):
    ack()
    user_id = body.get('user_id', 'unknown_user')
    channel_id = body.get('channel_id')
    if is_user_authorized(user_id) or is_temp_user_authorized(user_id):
        pass
    else:
        say(
            blocks = [
                {
                "type": "divider"  # Added a divider block for better UI separation
                },
                {
                    "type": "section",
                    "block_id": "sev1_section678",
                    "text": {
                    "type": "mrkdwn",
                    "text": f" \n Hey, \n <@{user_id}> Currently you do not have permission to perfom this opration. Please contact your admin or manager to authorise you we already sent request to them."
                    }
                }
            ]
        )
        client.chat_postMessage(
            channel='channel_id',
            blocks = [
            {
                "type": "divider"  # Added a divider block for better UI separation
            },
            {
                "type": "section",
                "block_id": "sev1_section678",
                "text": {
                    "type": "mrkdwn",
                    "text": f" \n Hey, \n <@{user_id}> is trying to access sev1 plan. \n would you like to give him permission to perform this action?"
                    }
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "block_id": "actionblock789",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Authorised",
                            "emoji": True
                        },
                        "value": channel_id,
                        "style": "primary",
                        "action_id": "grant_permanent"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Temporary Authorised",
                            "emoji": True
                        },
                        "value": channel_id,
                        "action_id": "grant_temporary"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Deny",
                            "emoji": True
                        },
                        "value": channel_id,
                        "style": "danger",
                        "action_id": "grant_deny"
                    }
                ]
            }
            ]
        )
        return
    say(
        blocks = [
            {
                "type": "divider"  # Added a divider block for better UI separation
            },
            {
                "type": "section",
                "block_id": "sev1_section678",
                "text": {
                    "type": "mrkdwn",
                    "text": f" \n Hey <@{user_id}>, \nPlease select the servers which are facing issues."
                },
                "accessory": {
                    "action_id": "sev1_select_option",
                    "type": "multi_static_select",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "Select an option",
                        "emoji": True
                    },
                    "options": front_as_back
                },
            },
            {
                "type": "divider"
            },
            {
                "type": "actions",
                "block_id": "actionblock789",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Submit",
                            "emoji": True
                        },
                        "style": "primary",
                        "confirm": {
                            "title": {
                                "type": "plain_text",
                                "text": "Are you sure?"
                            },
                            "text": {
                                "type": "mrkdwn",
                                "text": "Do you really want to check the selected servers?"
                            },
                            "confirm": {
                                "type": "plain_text",
                                "text": "Yes"
                            },
                            "deny": {
                                "type": "plain_text",
                                "text": "No"
                            }
                        },
                        "value": "submit_client_id",
                        "action_id": "sev1_submit_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Abort",
                            "emoji": True
                        },
                        "style": "danger",
                        "value": "abort_action",
                        "action_id": "sev1_abort_button"
                    }
                ]
            }
        ]
    )

@app.action("grant_permanent")
def grant_permanent(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    ts = body["message"]["ts"]
    add_authorized_user(user_id)

    client.chat_update(
        channel=channel_id,
        ts = ts,
        text=f"/sev1 = Permission has been granted to <@{user_id}>"
    )

    client.chat_postMessage(
        channel=body["actions"][0]["value"],
        text=f"hi <@{user_id}>, you are now Authorised. to perform /sev1 :)"
    )

@app.action("grant_temporary")
def grant_temporary(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    ts = body["message"]["ts"]
    add_temp_user(user_id)

    client.chat_update(
        channel=channel_id,
        ts = ts,
        text=f"/sev1 = Temporary permission has been granted to <@{user_id}>"
    )

    client.chat_postMessage(
        channel=body["actions"][0]["value"],
        text=f"hi <@{user_id}>, you are now Authorised to perform /sev1 task for once."
    )

@app.action("grant_deny")
def grant_deny(ack, client, body):
    ack()
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    ts = body["message"]["ts"]

    client.chat_update(
        channel=channel_id,
        ts = ts,
        text=f"Request has been denied for <@{user_id}>."
    )

    client.chat_postMessage(
        channel=body["actions"][0]["value"],
        text=f"sorry <@{user_id}>, your request to access seviour plan has been denied by your admin."
    )

@app.action("sev1_select_option")
def handle_option(ack):
    ack()

@app.action("sev1_submit_button")
def sev1_handle_button(ack, body, client):
    ack()
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    ts = body["message"]["ts"]
    state_values = body["state"]["values"]
    print(channel_id)


    client.chat_update(
        channel=channel_id,
        ts = ts,
        text="ok, let me check the servers Frist."
    )

    selected_option = state_values['sev1_section678']['sev1_select_option']['selected_options']

    final_list = []
    working = []
    for i in selected_option:
        print(i)
        client.chat_update(
        channel=channel_id,
        ts = ts,
        text=f"cheking for {i['text']['text']} Server."
        )
        output = subprocess.run(
        ["ping", "-c", "4", f"{i['value']}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
        )
        
        output_str = output.stdout.decode()
        # Determine the status message
        if "0% packet loss" in output_str or "bytes from" in output_str:
            final_list.append(i['value'])
            client.chat_update(
                channel=channel_id,
                ts = ts,
                text=f"Server {i['text']['text']} is up :)"
            )
        else:
            final_list.append(i['value'])
            client.chat_update(
                channel=channel_id,
                ts = ts,
                text=f"Server {i['text']['text']} is down :("
            )

    if len(final_list) > 0:
        temp = []
        for ip_address in final_list:
            name = ip.get(ip_address, "Name not found")  # Default message if IP is not found
            temp.append(name)
        client.chat_update(
        channel=channel_id,
        ts = ts,
        text=f"These Server seems down {', '.join(temp)}. No worries I will create them using latest backup whatever we have in s3 and come back to you as soon as possiable!"
        )
        with open('temp_access.txt', 'w'):
            pass
        instance.create_instances(temp, channel_id, user_id)
        
@app.action("sev1_abort_button")
def sev1_handle_abort(ack, body, client):
    ack()
    channel_id = body["channel"]["id"]
    ts = body["message"]["ts"]

    client.chat_delete(
        channel=channel_id,
        ts=ts
    )
    with open('temp_access.txt', 'w'):
        pass

# Start your app
if __name__ == "__main__":
    SocketModeHandler(app, os.getenv('App_token')).start()
