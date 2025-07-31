async function hello(){
    let [tab] = await chrome.tabs.query({active: true, currentWindow: true});
    await chrome.scripting.executeScript({
        target: {tabId: tab.id},
        func: () => {
            document.body.style.setProperty('background-color', 'yellow', 'important');
        }
    });
}
document.getElementById('btn').addEventListener('click', hello);