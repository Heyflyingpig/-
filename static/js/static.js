// 通用功能
document.addEventListener('DOMContentLoaded', function() {
    // 自动隐藏闪现消息
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            setTimeout(() => {
                alert.style.display = 'none';
            }, 500);
        }, 3000);
    });
    
    // 添加表单验证
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const requiredInputs = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredInputs.forEach(input => {
                if (!input.value.trim()) {
                    isValid = false;
                    
                    // 创建或更新错误提示
                    let errorMsg = input.nextElementSibling;
                    if (!errorMsg || !errorMsg.classList.contains('error-message')) {
                        errorMsg = document.createElement('div');
                        errorMsg.className = 'error-message';
                        input.parentNode.insertBefore(errorMsg, input.nextSibling);
                    }
                    
                    errorMsg.textContent = '此字段不能为空';
                    errorMsg.style.color = 'red';
                    errorMsg.style.fontSize = '0.8rem';
                    errorMsg.style.marginTop = '5px';
                    
                    // 添加输入事件以清除错误
                    input.addEventListener('input', function() {
                        if (this.value.trim()) {
                            errorMsg.textContent = '';
                        }
                    });
                }
            });
            
            if (!isValid) {
                e.preventDefault();
            }
        });
    });
});

// 聊天页面特定功能
if (document.querySelector('.chat-container')) {
    document.addEventListener('DOMContentLoaded', function() {
        const chatMessages = document.getElementById('chat-messages');
        const userInput = document.getElementById('user-input');
        const sendBtn = document.getElementById('send-btn');
        
        // 滚动到最新消息
        function scrollToBottom() {
            chatMessages.scrollTop = chatMessages.scrollHeight;
        }
        
        scrollToBottom();
        
        // 设置输入框自动调整高度
        userInput.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
            
            // 限制最大高度
            if (parseInt(this.style.height) > 150) {
                this.style.height = '150px';
                this.style.overflowY = 'auto';
            } else {
                this.style.overflowY = 'hidden';
            }
        });
        
        // 处理回车键发送
        userInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (sendBtn && userInput.value.trim()) {
                    sendBtn.click();
                }
            }
        });
        
        // 在接收消息时添加打字机效果
        window.typeWriter = function(element, text, speed = 30, callback) {
            let i = 0;
            element.textContent = '';
            
            function typing() {
                if (i < text.length) {
                    element.textContent += text.charAt(i);
                    i++;
                    setTimeout(typing, speed);
                } else if (callback) {
                    callback();
                }
            }
            
            typing();
        };
    });
}

// 控制面板特定功能
if (document.querySelector('.dashboard')) {
    document.addEventListener('DOMContentLoaded', function() {
        const modelList = document.getElementById('model-list');
        const createSessionBtn = document.getElementById('create-session-btn');
        
        if (createSessionBtn && modelList) {
            createSessionBtn.addEventListener('click', function() {
                if (modelList.style.display === 'none' || modelList.style.display === '') {
                    // 获取可用模型
                    fetch('/api/models')
                        .then(response => response.json())
                        .then(data => {
                            if (data.models && data.models.length > 0) {
                                modelList.innerHTML = '';
                                
                                data.models.forEach(model => {
                                    const form = document.createElement('form');
                                    form.method = 'POST';
                                    form.action = '/create_session';
                                    
                                    const modelIdInput = document.createElement('input');
                                    modelIdInput.type = 'hidden';
                                    modelIdInput.name = 'model_id';
                                    modelIdInput.value = model.m_id;
                                    form.appendChild(modelIdInput);
                                    
                                    const modelNameInput = document.createElement('input');
                                    modelNameInput.type = 'hidden';
                                    modelNameInput.name = 'model_name';
                                    modelNameInput.value = model.m_name;
                                    form.appendChild(modelNameInput);
                                    
                                    const submitBtn = document.createElement('button');
                                    submitBtn.type = 'submit';
                                    submitBtn.className = 'model-option';
                                    submitBtn.innerHTML = `
                                        <h4>${model.m_name}</h4>
                                        <p>版本: ${model.version}</p>
                                        <p>${model.describ || '无描述'}</p>
                                    `;
                                    form.appendChild(submitBtn);
                                    
                                    modelList.appendChild(form);
                                });
                                
                                modelList.style.display = 'grid';
                                
                                // 添加点击外部关闭模型列表
                                document.addEventListener('click', function closeModelList(e) {
                                    if (!modelList.contains(e.target) && e.target !== createSessionBtn) {
                                        modelList.style.display = 'none';
                                        document.removeEventListener('click', closeModelList);
                                    }
                                });
                            } else {
                                modelList.innerHTML = '<p class="empty-message">没有可用的模型</p>';
                                modelList.style.display = 'block';
                            }
                        })
                        .catch(error => {
                            console.error('获取模型失败:', error);
                            modelList.innerHTML = '<p class="empty-message">加载模型时出错</p>';
                            modelList.style.display = 'block';
                        });
                } else {
                    modelList.style.display = 'none';
                }
            });
        }
    });
}