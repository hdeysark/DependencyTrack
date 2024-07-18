pipeline {
    agent any

    environment {
        API_KEY = credentials('depTrack_local_API_KEY')
        BASE_URL = credentials('depTrack_local_baseurl')
    }

    stages {
        stage('Start') {
            steps{
                echo 'Start'
            }
        }

        stage('Run') {
            steps {
                echo "$API_KEY"
                echo "$BASE_URL"
                sh 'python3 importstack.py'
            }
        }

        stage ('Complete') {
            steps {
                echo 'Completed'
            }
        }
    }
}