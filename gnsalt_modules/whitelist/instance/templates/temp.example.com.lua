{%- set white_list_ls = white_list.split('/') -%}
list={
{%- for ip in white_list_ls %}
"{{ ip }}",
{%- endfor %}
 }
if ngx.var.http_x_forwarded_for == nil then
        if string.find(ngx.var.remote_addr , "^10.232")  then
                 return
        end
else
        if string.find(ngx.var.http_x_forwarded_for , "^10.232") then
                return
        end
        sn=string.find(ngx.var.http_x_forwarded_for,",")
        if sn == nil then
                xip=ngx.var.http_x_forwarded_for
        else
                xip=string.sub(ngx.var.http_x_forwarded_for,1,sn-1)
        end
        for i = 1,#list do
            if xip == list[i] then
                    return
            end
        end
end
ngx.exit(403)
