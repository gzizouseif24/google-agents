api_server creations : 

$headers = @{ 'Content-Type' = 'application/json' }; $body = @{ state = @{ Temperature = 'celsius'; City = 'Tunis' } } | ConvertTo-Json; Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/apps/multi_tool_agent/users/u_00001/sessions/s_00001' -Headers $headers -Body $body


$headers = @{ 'Content-Type' = 'application/json' }; $body = @{ app_name = 'multi_tool_agent'; user_id = 'u_00001'; session_id = 's_00001'; new_message = @{ role = 'user'; parts = @(@{ text = 'Hey whats the weather ?' }) } } | ConvertTo-Json -Depth 10; Invoke-RestMethod -Method Post -Uri 'http://localhost:8000/run' -Headers $headers -Body $body