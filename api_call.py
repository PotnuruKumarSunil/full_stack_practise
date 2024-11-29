from flask import Flask, render_template, request, redirect, url_for
import jenkins
import time
import csv
from datetime import datetime
 
app = Flask(__name__)
 
class JenkinsJobTrigger:
    jenkins_url = "http://titan:8080"  # Base URL without login path
    username = "Runtest"
    password = "Runtest"
 
    def __init__(self):
        self.server = jenkins.Jenkins(self.jenkins_url, username=self.username, password=self.password)
 
    def trigger_job(self, job_name, parameters=None):
        trigger_time = datetime.now().isoformat()  # Capture the trigger time
        try:
            if parameters:
                self.server.build_job(job_name, parameters)
                print(f"Triggered job '{job_name}' with parameters: {parameters} at {trigger_time}")
            else:
                self.server.build_job(job_name)
                print(f"Triggered job '{job_name}' without parameters at {trigger_time}.")
            return trigger_time  # Return the trigger time for reporting
        except jenkins.NotFoundException:
            print(f"Job '{job_name}' not found.")
        except jenkins.JenkinsException as e:
            print(f"Jenkins error: {e}")
        except Exception as e:
            print(f"An error occurred: {e}")
 
    @staticmethod
    def read_parameters_from_csv(file_path):
        job_details = []
        try:
            with open(file_path, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    job_name = row['Job_Name'].strip()
                    parameters = {
                        "RELEASE": row['RELEASE'].strip(),
                        "TASK": row['TASK'].strip(),
                        "MODULE_NAME": row['MODULE_NAME'].strip(),
                        "PMS_USERNAME": row['PMS_USERNAME'].strip(),
                        "RUN_MODE": row['RUN_MODE'].strip(),
                        "ROBOT_SCRIPT_NAMES": row['ROBOT_SCRIPT_NAMES'].strip(),
                        "TESTBED": row['TESTBED'].strip(),
                    }
                    scheduled_time = row['Time'].strip()  # Read the scheduled time
                    run_job = row['RUN_JOB'].strip()  # Read the "Yes" or "No" flag
                    job_details.append((job_name, parameters, scheduled_time, run_job))
                    print(f"Read job: {job_name}, parameters: {parameters}, scheduled_time: {scheduled_time}, run_job: {run_job}")
        except FileNotFoundError:
            print(f"Parameter file '{file_path}' not found.")
        except Exception as e:
            print(f"An error occurred while reading parameters: {e}")
        return job_details
 
    def generate_job_report(self, job_name, parameters, trigger_time, report_file_path):
        try:
            job_info = self.server.get_job_info(job_name)
            builds = job_info['builds']
 
            with open(report_file_path, mode='w', newline='') as report_file:
                writer = csv.writer(report_file)
                writer.writerow(['Build Number', 'Result', 'Duration (ms)', 'Timestamp', 'Trigger Time', 'Job URL'] + list(parameters.keys()))
 
                job_url = f"{self.jenkins_url}/job/{job_name}"
 
                for build in builds:
                    build_number = build['number']
                    build_info = self.server.get_build_info(job_name, build_number)
                    result = build_info['result']
                    duration = build_info['duration']
                    timestamp = datetime.fromtimestamp(build_info['timestamp'] / 1000).isoformat()
 
                    row = [build_number, result, duration, timestamp, trigger_time, job_url] + [parameters.get(key, '') for key in parameters.keys()]
                    writer.writerow(row)
 
            print(f"Report generated: {report_file_path}")
 
        except jenkins.NotFoundException:
            print(f"Job '{job_name}' not found for reporting.")
        except jenkins.JenkinsException as e:
            print(f"Jenkins error while generating report: {e}")
        except Exception as e:
            print(f"An error occurred while generating report: {e}")
 
@app.route('/')
def index():
    return render_template('index.html')
 
@app.route('/trigger', methods=['POST'])
def trigger_jobs():
    job_details = JenkinsJobTrigger.read_parameters_from_csv(r'path_to_your_csv_file.csv')
    jenkins_trigger = JenkinsJobTrigger()
 
    for job_name, parameters, scheduled_time, run_job in job_details:
        if run_job.lower() == "yes":
            trigger_time = jenkins_trigger.trigger_job(job_name, parameters)
            report_file_path = f'C:/Users/chandanik/Desktop/Jenkins/job_report_{job_name}.csv'
            jenkins_trigger.generate_job_report(job_name, parameters, trigger_time, report_file_path)
 
    return redirect(url_for('index'))
 
if __name__ == "__main__":
    app.run(debug=True)